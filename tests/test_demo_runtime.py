"""Connected Demo tests: fixed SIMULATED input, no real credential/provider."""
import ast
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
from dataclasses import replace
from fractions import Fraction
from http.client import HTTPConnection
from io import StringIO
import json
import os
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch
from uuid import uuid4

from snapshot_loader.demo_composition import analyze
from snapshot_loader.demo_session import DemoSession, DemoError, exact, display, MAX_INTENTS
from snapshot_loader.demo_server import DemoServer, MAX_BODY
from snapshot_loader.explanation_q3 import explain_q3
from snapshot_loader.explanation_seam import ANSWER_KIND_LITERALS


class Stub:
    def __init__(self, value=None, raises=False):
        self.calls = []; self.value = value; self.raises = raises

    def explain(self, projection):
        self.calls.append(projection)
        if self.raises:
            raise RuntimeError("SECRET-PROVIDER-BODY")
        if self.value is not None:
            return self.value
        return {"answer_kind": "MOQ_RAISED_RECOMMENDATION_ABOVE_SHORTAGE", "evidence": ["ShortageQty", "BasePurchaseNeed", "ApplicableMOQ", "MOQAdjustmentQty", "RecommendedPurchaseQty"], "uncertainty": [], "human_decision_required": True}


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.s = DemoSession(); self.addCleanup(self.s.close)
        self.s.execute({"op": "initialize", "intent": "initial-intent", "session": self.s.session})

    def command(self, op, **args):
        v = self.s.snapshot()
        return {"op": op, "intent": uuid4().hex, "session": v["session"], "run": v["run"], "review": v["review"]["id"], **args}

    def act(self, op, **args):
        return self.s.execute(self.command(op, **args))

    def test_composition_evidence_and_runtime_dependencies(self):
        v = self.s.snapshot()
        self.assertEqual([v['facts'][k] for k in ('shortage','base','moq','adjustment','recommended')], ['30','30','100','70','100'])
        self.assertEqual((v['facts']['plant_id'],v['facts']['material_code']), ('SIM-P1','SIM-M2'))
        self.assertEqual(v['binding']['analysis_date'], '2026-10-01')
        self.assertTrue(self.s.result.import_report.accepted)
        self.assertEqual(self.s.run.accepted_content_view_digest, self.s.result.import_report.accepted_package.content_view_digest)
        for name in ('demo_composition','demo_session','demo_server'):
            tree=ast.parse(Path('snapshot_loader',name+'.py').read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.ImportFrom):
                    self.assertNotIn('tests',node.module or '')
                    self.assertNotIn('scripts',node.module or '')

    def test_initialize_refresh_second_view_and_new_run(self):
        a=self.s.snapshot(); b=self.s.execute({'op':'initialize','intent':'another-initial','session':self.s.session})
        self.assertEqual(a,b)
        self.act('open_review'); old=self.s.review; draft=self.s.draft
        result=self.act('new_analysis')
        self.assertNotEqual(a['run'],result['run'])
        self.assertEqual(a['binding']['accepted_content_view_digest'],result['binding']['accepted_content_view_digest'])
        self.assertTrue(old.is_stale(self.s.run)); self.assertTrue(draft.is_stale(self.s.run))
        self.assertFalse(draft.is_actionable(self.s.run))
        self.act('open_review'); self.assertIsNot(old,self.s.review)
        self.assertIsNone(self.s.review.decision)
        self.assertTrue(old.is_stale(old.analysis_run))

    def test_approve_and_real_decision_identity(self):
        self.act('open_review'); v=self.act('approve')
        self.assertEqual(v['draft']['quantity'],exact(Fraction(100)))
        self.assertIs(self.s.draft.decision,self.s.review.decision)
        self.assertTrue(v['canDraft']); self.assertFalse(v['canDecide'])
        with self.assertRaises(DemoError): self.act('approve')

    def test_override_exact_and_deterministic_unchanged(self):
        self.act('open_review')
        value='+000120.000000000000000000000000000000000000001'
        request=self.command('override',quantity=value,reason='SIMULATED reason')
        v=self.s.execute(request)
        self.assertEqual(v['draft']['quantity'],exact(Fraction(value)))
        self.assertEqual(v['facts']['recommended'],'100')
        self.assertIn(value,self.s.intents[request['intent']][0])
        self.assertNotIn('raw',self.s.review.decision.to_dict())

    def test_long_integer_and_rational_wire(self):
        self.act('open_review'); number='9'*150
        self.assertEqual(self.act('override',quantity=number,reason='reason')['draft']['quantity']['numerator'],number)
        self.assertEqual(exact(Fraction(10**180,3)),{'numerator':str(10**180),'denominator':'3'})
        self.assertEqual(display(Fraction(1,3)),'1/3')

    def test_invalid_quantity_reason_and_moq(self):
        self.act('open_review')
        for value in ['99.999','0','-1',' 120','120 ','1e3','1,000','NaN','120.','']:
            with self.subTest(value=value),self.assertRaises(DemoError): self.act('override',quantity=value,reason='reason')
            self.assertIsNone(self.s.review.decision)
        with self.assertRaises(DemoError): self.act('override',quantity='120',reason=' ')
        self.assertTrue(self.act('override',quantity='100',reason='reason')['canDraft'])

    def test_reject_stale_and_no_inheritance(self):
        self.act('open_review'); self.act('reject',reason='not buying')
        self.assertFalse(self.s.snapshot()['canDraft'])
        self.assertEqual(self.s.snapshot()['review']['decision']['reason'],'not buying')
        self.act('new_analysis'); self.act('open_review')
        self.assertIsNone(self.s.review.decision)
        self.assertTrue(self.act('approve')['canDraft'])

    def test_replay_conflicts_and_capacity(self):
        self.act('open_review'); request=self.command('approve')
        a=self.s.execute(request); self.assertEqual(a,self.s.execute(request))
        with self.assertRaises(DemoError): self.s.execute({**request,'op':'reject','reason':'x'})
        self.act('new_analysis'); self.act('open_review')
        self.assertFalse(self.s.execute(request)['canDraft'])
        self.assertIsNone(self.s.review.decision)
        with self.assertRaises(DemoError): self.s.execute({**request,'intent':uuid4().hex})
        self.s.intents={str(i):('',None) for i in range(MAX_INTENTS)}
        with self.assertRaises(DemoError): self.act('new_analysis')

    def test_restart_refs_and_competing_decisions(self):
        self.act('open_review'); requests=[self.command('approve'),self.command('reject',reason='no')]
        def run(r):
            try: self.s.execute(r); return True
            except DemoError: return False
        with ThreadPoolExecutor(2) as pool: self.assertEqual(sorted(pool.map(run,requests)),[False,True])
        fresh=DemoSession(); self.addCleanup(fresh.close)
        with self.assertRaises(DemoError): fresh.execute(requests[0])
        with self.assertRaises(DemoError): fresh.execute({'op':'initialize','intent':'old-initial','session':self.s.session})

    def test_q3_validator_unavailable_and_immutable_review(self):
        self.s.provider=Stub(); v=self.act('explain')
        self.assertTrue(v['hasExplanation']); self.assertEqual(len(self.s.provider.calls),1)
        self.act('open_review'); projection=self.s.review.projection
        with self.assertRaises(DemoError): self.act('explain')
        self.assertIs(projection,self.s.review.projection)
        self.act('new_analysis'); self.assertFalse(self.s.snapshot()['hasExplanation'])
        self.assertTrue(self.act('explain')['hasExplanation'])
        self.assertIs(projection,self.s.review.projection)
        self.assertTrue(self.s.snapshot()['review']['stale'])
        self.s.provider=Stub({'answer':'SECRET-PROVIDER-BODY'})
        self.assertFalse(self.act('explain')['hasExplanation'])
        self.s.provider=Stub(raises=True)
        self.assertFalse(self.act('explain')['hasExplanation'])
        self.assertNotIn('SECRET',json.dumps(self.s.snapshot()))
        self.act('open_review'); self.assertTrue(self.act('approve')['canDraft'])

    def test_cross_run_explanation_rejected(self):
        previous=explain_q3(self.s.result.procurement_recommendation,Stub(),plant_id='SIM-P1',material_code='SIM-M2')
        self.act('new_analysis')
        with patch('snapshot_loader.demo_session.explain_q3',return_value=previous):
            with self.assertRaises(DemoError): self.act('explain')
        self.assertIsNone(self.s.explanation)

    def test_failed_new_analysis_does_not_change_current_run(self):
        before=self.s.snapshot()
        with patch('snapshot_loader.demo_session.analyze',side_effect=RuntimeError('secret')):
            with self.assertRaises(DemoError): self.act('new_analysis')
        self.assertEqual(before,self.s.snapshot())


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); (self.root/'index.html').write_text('SIMULATED')
        self.server=DemoServer(('127.0.0.1',0),self.root)
        self.thread=Thread(target=self.server.serve_forever,kwargs={'poll_interval':0.01}); self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(3)

    def request(self,body=None,headers=None,path='/demo/intent',method='POST'):
        connection=HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        h={'Origin':self.server.origin,'Content-Type':'application/json',**(headers or {})}
        connection.request(method,path,body=body,headers=h)
        response=connection.getresponse(); data=response.read(); result=(response.status,data,dict(response.getheaders()))
        connection.close(); return result

    def test_host_origin_and_static_routes(self):
        body=json.dumps({'op':'initialize','intent':'test-init','session':self.server.session.session})
        self.assertEqual(self.request(body)[0],200)
        for h in [{'Host':'evil.test'},{'Host':'localhost:80'},{'Origin':'null'},{'Origin':'http://evil.test'},{'Origin':''}]:
            self.assertEqual(self.request(body,h)[0],403)
        for path in ['/','/procurement/SIM-M2']:
            status,_,headers=self.request(path=path,method='GET'); self.assertEqual(status,200)
            self.assertNotIn('Access-Control-Allow-Origin',headers)
        for path in ['/../pyproject.toml','/%2e%2e/secret','/assets/../../secret','/snapshot_loader/demo_server.py','http://evil.test/','/proxy?url=x']:
            self.assertGreaterEqual(self.request(path=path,method='GET')[0],400)
        with self.assertRaises(ValueError): DemoServer(('0.0.0.0',0),self.root)

    def test_strict_json_unknown_body_and_sanitized_error(self):
        for body in ['{','[]','{"op":"initialize","op":"approve","intent":"test-init"}', '{"op":NaN}',json.dumps({'op':'exec','intent':'test-init'}),json.dumps({'op':'initialize','intent':'test-init','extra':'x'})]:
            self.assertGreaterEqual(self.request(body)[0],400)
        self.assertEqual(self.request('x'*(MAX_BODY+1))[0],413)
        with patch.object(self.server.session,'execute',side_effect=RuntimeError('SECRET-PROVIDER-BODY')),redirect_stderr(StringIO()) as logs:
            status,data,_=self.request('{"op":"initialize","intent":"test-init"}')
        self.assertEqual(status,503); self.assertNotIn('SECRET',data.decode()+logs.getvalue())

    def test_invalid_framing_missing_origin_and_raw_headers(self):
        for headers in ['Content-Length: 2\r\nContent-Length: 2\r\n','Transfer-Encoding: chunked\r\n','Content-Length: -1\r\n','Content-Length: 2\r\n']:
            with socket.create_connection(self.server.server_address,timeout=5) as sock:
                sock.sendall((f'POST /demo/intent HTTP/1.0\r\nHost: {self.server.allowed_host}\r\nContent-Type: application/json\r\n'+headers+'\r\n{}').encode())
                self.assertIn(b'403',sock.recv(4096)) # missing Origin fails before body parsing
        for headers in ['Content-Length: 2\r\nContent-Length: 2\r\n','Transfer-Encoding: chunked\r\n','Content-Length: -1\r\n']:
            with socket.create_connection(self.server.server_address,timeout=5) as sock:
                sock.sendall((f'POST /demo/intent HTTP/1.0\r\nHost: {self.server.allowed_host}\r\nOrigin: {self.server.origin}\r\nContent-Type: application/json\r\n'+headers+'\r\n{}').encode())
                self.assertIn(b'400',sock.recv(4096))

    def test_build_required_symlink_containment_and_shutdown_cleanup(self):
        empty=self.root/'empty'; empty.mkdir()
        with self.assertRaises(ValueError): DemoServer(('127.0.0.1',0),empty)
        # Test resolved escape independently of Windows symlink-creation privileges.
        from snapshot_loader.demo_server import build_assets
        original=Path.resolve
        def escape(path,*args,**kwargs):
            if path.name=='index.html': return self.root.parent/'outside.html'
            return original(path,*args,**kwargs)
        with patch.object(Path,'resolve',escape),self.assertRaises(ValueError): build_assets(self.root)
        owned=self.server.session.temp.name
        self.server.session.close()
        self.assertFalse(Path(owned).exists())
        self.assertEqual(self.request(path='/demo/state',method='GET')[0],409)

    def test_environment_credential_is_never_acquired(self):
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'SENTINEL-NOT-A-CREDENTIAL'}),patch('snapshot_loader.deepseek_provider.provider_from_environment',side_effect=AssertionError('must not acquire')):
            s=DemoSession(); self.addCleanup(s.close)
            v=s.execute({'op':'initialize','intent':'test-init','session':s.session})
            v=s.execute({'op':'explain','intent':'explain-test','session':v['session'],'run':v['run'],'review':None})
            self.assertFalse(v['hasExplanation'])
            self.assertNotIn('SENTINEL',json.dumps(v))

    def test_http_exact_lifecycle_and_stub_evidence(self):
        self.server.session.provider=Stub()
        def op(name,**args):
            v=json.loads(self.request(path='/demo/state',method='GET')[1])
            data={'op':name,'intent':uuid4().hex,'session':v['session'],**args}
            if name!='initialize': data.update(run=v['run'],review=v['review']['id'])
            status,body,_=self.request(json.dumps(data))
            self.assertEqual(status,200,body)
            return json.loads(body)
        a=op('initialize'); self.assertTrue(op('explain')['hasExplanation'])
        op('open_review')
        raw='+000120.000000000000000000000000000000000000001'
        v=op('override',quantity=raw,reason='SIMULATED exact HTTP')
        self.assertEqual(v['draft']['quantity'],exact(Fraction(raw)))
        self.assertEqual(v['facts']['recommended'],'100')
        self.assertIs(self.server.session.review.decision,self.server.session.draft.decision)
        v=op('new_analysis'); self.assertTrue(v['review']['stale']); self.assertFalse(v['canDraft'])
        self.assertEqual(v['binding']['accepted_content_view_digest'],a['binding']['accepted_content_view_digest'])
        self.assertTrue(op('explain')['hasExplanation'])
        self.assertIsNone(op('open_review')['review']['decision'])
        self.assertFalse(op('reject',reason='no')['canDraft'])

    def test_static_snapshot_has_no_live_filesystem_or_proxy(self):
        (self.root/'secret.txt').write_text('NOT-SERVED')
        self.assertEqual(self.request(path='/secret.txt',method='GET')[0],404)
        self.assertEqual(self.request(path='/demo/proxy',body='{}')[0],404)
        self.assertEqual(self.request(path='/demo/state?path=secret.txt',method='GET')[0],400)
        self.assertEqual(self.request(method='OPTIONS')[0],501)
        self.assertEqual(self.request('{"op":"initialize","intent":"test-init"}',{'Content-Type':'text/plain'})[0],400)

    def test_framing_timeout_unknown_bindings_and_secret_headers(self):
        with socket.create_connection(self.server.server_address,timeout=5) as sock:
            sock.sendall((f'POST /demo/intent HTTP/1.0\r\nHost: {self.server.allowed_host}\r\nOrigin: {self.server.origin}\r\nContent-Type: application/json\r\nContent-Length: 20\r\n\r\n{{}}').encode())
            self.assertIn(b'503',sock.recv(4096))
        status,body,headers=self.request(json.dumps({'op':'initialize','intent':'test-init','session':'old-session'}),{'Authorization':'Bearer SECRET-SENTINEL'})
        self.assertEqual(status,409)
        self.assertNotIn('SECRET',body.decode()+json.dumps(headers))
        with socket.create_connection(self.server.server_address,timeout=5) as sock:
            sock.sendall((f'GET / HTTP/1.0\r\nHost: {self.server.allowed_host}\r\nHost: evil.test\r\n\r\n').encode())
            self.assertIn(b'403',sock.recv(4096))

    def test_bounded_connection_admission(self):
        # Every admitted socket owns one semaphore slot until its handler exits.
        from snapshot_loader.demo_server import MAX_CONNECTIONS
        sockets=[]
        try:
            for _ in range(MAX_CONNECTIONS):
                s=socket.create_connection(self.server.server_address,timeout=2)
                s.sendall(b'GET / HTTP/1.0\r\n'); sockets.append(s)
            import time
            deadline=time.monotonic()+2
            while self.server.slots._value and time.monotonic()<deadline: time.sleep(.01)
            self.assertEqual(self.server.slots._value,0)
            with socket.create_connection(self.server.server_address,timeout=2) as extra:
                try: self.assertEqual(extra.recv(100),b'')
                except ConnectionResetError: pass
        finally:
            for s in sockets: s.close()


if __name__ == '__main__': unittest.main()

