"""Subprocess boundary regressions; never invokes Core or user media."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import core_clients

class CoreClientBoundaryTests(unittest.TestCase):
    def test_bootstrap_is_isolated_and_uses_exact_core_paths(self):
        root=Path("D:/project with spaces/quote'owner/core")
        command=core_clients._command(root,"experimental.shared_data","info")
        self.assertEqual(command[1:4],["-B","-I","-c"])
        tree=ast.parse(command[4])
        self.assertEqual(ast.literal_eval(tree.body[1].value),[str(root),str(root/"src")])
        self.assertEqual(command[5:],["info"])
        self.assertNotIn("-m",command)

    @patch("core_clients.subprocess.run")
    def test_info_uses_consumer_cwd_and_never_core_cwd(self,run):
        run.return_value=SimpleNamespace(stdout='{"ok":true}',stderr="",returncode=0)
        consumer=Path.cwd().resolve()
        client=core_clients.SharedDataClient(consumer,core_root=consumer/"core")
        client.info()
        args,kwargs=run.call_args
        self.assertEqual(kwargs["cwd"],consumer)
        self.assertNotEqual(kwargs["cwd"],client.core_root)
        self.assertEqual(args[0][1:4],["-B","-I","-c"])
        self.assertEqual(kwargs["env"]["PYTHONDONTWRITEBYTECODE"],"1")

    @patch("core_clients.subprocess.run")
    def test_manifest_verify_has_consumer_contract(self,run):
        run.side_effect=[SimpleNamespace(stdout='{"ok":true,"contract_version":2}',stderr="",returncode=0),SimpleNamespace(stdout='{"ok":true,"capability_version":1}',stderr="",returncode=0)]
        consumer=Path.cwd().resolve()
        core_clients.public_core_manifest(consumer/"core",consumer_root=consumer)
        command=run.call_args_list[0].args[0]
        self.assertIn("--consumer-root",command)
        self.assertEqual(command[command.index("--consumer-root")+1],str(consumer))
        self.assertTrue(all(c.kwargs["cwd"]==consumer for c in run.call_args_list))

    @patch("core_clients.subprocess.run")
    def test_invoke_preserves_write_protection_and_payload(self,run):
        run.return_value=SimpleNamespace(stdout='{"ok":true,"result":{"count":0}}',stderr="",returncode=0)
        consumer=Path.cwd().resolve()
        client=core_clients.SharedDataClient(consumer,core_root=consumer/"core")
        self.assertEqual(client.invoke("source.list",{}),{"count":0})
        command=run.call_args.args[0]
        self.assertNotIn("--write",command)
        self.assertEqual(command[-1],"invoke")
        self.assertEqual(command.count("--protected-path"),4)
        self.assertEqual(json.loads(run.call_args.kwargs["input"]),{"operation":"source.list","arguments":{}})
        client.invoke("source.create",{},write=True)
        self.assertIn("--write",run.call_args.args[0])

    @patch("core_clients.subprocess.run")
    def test_core_or_descendant_cwd_is_rejected_before_launch(self, run):
        core=(Path.cwd()/"core").resolve()
        with self.assertRaises(core_clients.CoreClientError):
            core_clients.SharedDataClient(core,core_root=core)
        with self.assertRaises(core_clients.CoreClientError):
            core_clients._run_json(["unused"],core_root=core,consumer_root=core/"src")
        run.assert_not_called()

    @patch("core_clients.subprocess.run")
    def test_invalid_or_failed_response_does_not_become_success(self,run):
        for stdout,code in [("not-json",0),('{"ok":true}',1),('{"ok":false,"kind":"refused"}',0)]:
            with self.subTest(stdout=stdout,code=code):
                run.return_value=SimpleNamespace(stdout=stdout,stderr="rejected",returncode=code)
                with self.assertRaises(core_clients.CoreClientError):
                    core_clients._run_json(["unused"],core_root=Path.cwd()/"core",consumer_root=Path.cwd())

if __name__=="__main__":unittest.main()
