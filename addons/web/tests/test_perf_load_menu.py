
import json
from uuid import uuid4

from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestPerfSessionInfo(common.HttpCase):

    def test_performance_session_info(self):
        user = common.new_test_user(
            self.env,
            "session",
            email="session@in.fo",
            tz="UTC",
        )
        self.authenticate(user.login, "info")

        self.env.registry.clear_all_caches()
        # cold ormcache (only web: 43, all module: 131)
        with self.assertQueryCount(131):
            self.url_open(
                "/web/session/get_session_info",
                data=json.dumps({'jsonrpc': "2.0", 'method': "call", 'id': str(uuid4())}),
                headers={"Content-Type": "application/json"},
            )

        # cold fields cache - warm ormcache (only web: 7, all module: 22)
        with self.assertQueryCount(22):
            self.url_open(
                "/web/session/get_session_info",
                data=json.dumps({'jsonrpc': "2.0", 'method': "call", 'id': str(uuid4())}),
                headers={"Content-Type": "application/json"},
            )

    def test_load_web_menus_perf(self):
        self.env.registry.clear_all_caches()
        self.env.invalidate_all()
        # cold orm/fields cache (only web: 19, all module: 80)
        with self.assertQueryCount(80):
            self.env['ir.ui.menu'].load_web_menus(False)

        # cold fields cache - warm orm cache (only web: 6, all module: 635)
        self.env.invalidate_all()
        with self.assertQueryCount(635):
            self.env['ir.ui.menu'].load_web_menus(False)

    def test_load_menus_perf(self):
        self.env.registry.clear_all_caches()
        self.env.invalidate_all()
        # cold orm/fields cache (only web: 17, all module: 45)
        with self.assertQueryCount(45):
            self.env['ir.ui.menu'].load_menus(False)

        # cold fields cache - warm orm cache (only web: 0, all module: 1)
        self.env.invalidate_all()
        with self.assertQueryCount(1):
            self.env['ir.ui.menu'].load_menus(False)

    def test_visible_menu_ids(self):
        self.env.registry.clear_all_caches()
        self.env.invalidate_all()
        # cold ormcache (only web: 7, all module: 19)
        with self.assertQueryCount(19):
            self.env['ir.ui.menu']._visible_menu_ids()

        # cold fields cache - warm orm cache (only web: 1, all module: 1)
        self.env.invalidate_all()
        with self.assertQueryCount(1):
            self.env['ir.ui.menu']._visible_menu_ids()
