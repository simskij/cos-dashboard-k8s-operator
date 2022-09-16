# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest

from charms.cos_dashboard_k8s.v0.dashboard_info import DEFAULT_RELATION_NAME
from ops.model import ActiveStatus
from ops.testing import Harness

from charm import CosDashboardCharm

CONTAINER_NAME = "dashboard"



class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(CosDashboardCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin_with_initial_hooks()
        self.harness.set_leader(True)

    def test_dashboard_pebble_ready(self):

        initial_plan = self.harness.get_container_pebble_plan(CONTAINER_NAME)
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        expected_plan = {
            "services": {
                "sui": {
                    "override": "replace",
                    "summary": "sui",
                    "command": "/init",
                    "startup": "enabled",
                }
            },
        }

        container = self.harness.model.unit.get_container(CONTAINER_NAME)
        self.harness.charm.on.dashboard_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan(CONTAINER_NAME).to_dict()
        self.assertEqual(expected_plan, updated_plan)
        service = self.harness.model.unit.get_container(CONTAINER_NAME).get_service("sui")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_reconfigure_applications(self):
        rel_id = self.harness.add_relation(DEFAULT_RELATION_NAME, "rc")
        self.harness.add_relation_unit(rel_id, "rc/0")
        self.harness.update_relation_data(
            rel_id,
            "rc",
            {"name": "remote-charm", "url": "https://localhost", "icon": "some-cool-icon"},
        )

        data = self.harness.model.unit.get_container(CONTAINER_NAME).pull("/config/www/apps.json")
        self.assertEqual(
            data.read(),
            """{"apps": [{"name": "remote-charm", "url": "https://localhost", "icon": "some-cool-icon"}]}""",
        )
