import json
import tempfile
import unittest
from pathlib import Path
from tester_spin.models import Game, GameTestResult
from tester_spin.storage import Storage
from tester_spin.manual_review import render_review
from tester_spin.ui_game_index import retryable_games
from tester_spin.project_actions import export_reports, clear_history

class ManualValidationTests(unittest.TestCase):
    def test_persistent_reversible_scoped_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Storage(Path(tmp)/"db.sqlite3")
            for provider in ("bgaming", "belatra"):
                s.upsert_games([Game(provider,"game","Juego","demo")])
                s.record_result(GameTestResult(provider,"game","Juego","demo",2,1,1,"PARCIAL",error="compra rechazada"))
            s.set_manual_ok("bgaming","game","No tiene compras")
            s=Storage(s.path)
            g=s.get_game("bgaming","game")
            self.assertEqual(g.last_status,"PARCIAL")
            self.assertEqual(g.display_status,"OK MANUAL")
            self.assertEqual(retryable_games([g]),[])
            self.assertEqual(s.get_game("belatra","game").display_status,"PARCIAL")
            report=render_review(s.latest_results())
            self.assertIn("1 juegos para revisar",report)
            self.assertIn("OK MANUAL",report)
            root=Path(tmp)
            export_reports(root,s,lambda _: None)
            exported=json.loads((root/"test-evidence/bgaming/game/result.json").read_text(encoding="utf-8"))
            self.assertEqual(exported["status"],"PARCIAL")
            self.assertEqual(exported["manual_validation"]["note"],"No tiene compras")
            s.set_manual_ok("bgaming","game",enabled=False)
            self.assertEqual(s.get_game("bgaming","game").display_status,"PARCIAL")
            s.set_manual_ok("bgaming","game")
            s.record_result(GameTestResult("bgaming","game","Juego","demo",1,0,1,"ERROR"))
            self.assertEqual(s.get_game("bgaming","game").display_status,"ERROR")
            self.assertNotIn("manual_validation",next(r for r in s.latest_results() if r["provider"]=="bgaming"))

    def test_no_result_cannot_be_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=Storage(Path(tmp)/"db.sqlite3")
            s.upsert_games([Game("bgaming","game","Juego","demo")])
            with self.assertRaises(ValueError):
                s.set_manual_ok("bgaming","game")

    def test_ui_action_saves_and_cancel_does_not(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from tester_spin.app import TesterSpinApp
        game=Game("bgaming","game","Juego","demo")
        ui=SimpleNamespace(_worker=None, tree=Mock(), _games={"row":game},
                           storage=Mock(), _refresh_games=Mock(), _show_selected_game=Mock(),
                           _append_log=Mock(), status_var=Mock(), data_root=Path("unused"))
        ui.tree.selection.return_value=("row",)
        with patch("tester_spin.app.simpledialog.askstring",return_value=None):
            TesterSpinApp._set_selected_manual_ok(ui,True)
        ui.storage.set_manual_ok.assert_not_called()
        with patch("tester_spin.app.simpledialog.askstring",return_value="No tiene compras"), patch("tester_spin.manual_review.write_review"):
            TesterSpinApp._set_selected_manual_ok(ui,True)
        ui.storage.set_manual_ok.assert_called_once_with("bgaming","game","No tiene compras",enabled=True)
        with patch("tester_spin.manual_review.write_review"):
            TesterSpinApp._set_selected_manual_ok(ui,False)
        self.assertEqual(ui.storage.set_manual_ok.call_args.kwargs,{"enabled":False})
