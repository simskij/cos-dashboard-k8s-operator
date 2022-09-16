#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following post for a quick-start guide that will help you
develop a new k8s charm using the Operator Framework:

    https://discourse.charmhub.io/t/4208
"""

import json
import logging

from charms.cos_dashboard_k8s.v0.dashboard_info import (
    DashboardInfoConsumer,
    EntriesChangedEvent,
)
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus

logger = logging.getLogger(__name__)


class CosDashboardCharm(CharmBase):
    """Charm the service."""

    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.name = "cos-dashboard"
        self._info = DashboardInfoConsumer(charm=self)
        self.framework.observe(self.on.dashboard_pebble_ready, self._on_dashboard_pebble_ready)
        self.framework.observe(self._info.on.entries_changed, self._on_entries_changed)
        self._stored.set_default(things=[])

    def _on_dashboard_pebble_ready(self, event):
        """Define and start a workload using the Pebble API.

        TEMPLATE-TODO: change this example to suit your needs.
        You'll need to specify the right entrypoint and environment
        configuration for your specific workload. Tip: you can see the
        standard entrypoint of an existing container using docker inspect

        Learn more about Pebble layers at https://github.com/canonical/pebble
        """
        # Get a reference the container attribute on the PebbleReadyEvent
        container = event.workload
        # Define an initial Pebble layer configuration
        pebble_layer = {
            "summary": "sui layer",
            "description": "pebble config layer for sui",
            "services": {
                "sui": {
                    "override": "replace",
                    "summary": "sui",
                    "command": "/init",
                    "startup": "enabled",
                }
            },
        }
        container.add_layer("sui", pebble_layer, combine=True)
        container.autostart()
        container.push("/config/www/links.json", json.dumps(self.links), make_dirs=True)
        self._refresh_apps_list(self._info.entries)
        self.unit.status = ActiveStatus()

    def _on_entries_changed(self, event: EntriesChangedEvent):
        self._refresh_apps_list(event.apps)

    def _refresh_apps_list(self, apps):
        logger.info("Configuring %s application entries", len(apps))
        container = self.unit.get_container("dashboard")
        container.push("/config/www/apps.json", json.dumps({"apps": apps}), make_dirs=True)

    @property
    def links(self):
        """Get the links to show in the dashboard."""
        return {
            "bookmarks": [
                {
                    "category": "Documentation",
                    "links": [
                        {
                            "name": "Juju Operator Lifecycle Manager",
                            "url": "https://juju.is/docs/olm",
                        },
                        {
                            "name": "Canonical Observability Stack",
                            "url": "https://charmhub.io/topics/canonical-observability-stack",
                        },
                        {"name": "COS Lite", "url": "https://charmhub.io/cos-lite/"},
                    ],
                },
                {
                    "category": "Join the conversation",
                    "links": [
                        {"name": "Discourse", "url": "https://discourse.charmhub.io/"},
                        {"name": "Mattermost", "url": "https://chat.charmhub.io/"},
                        {"name": "COS Lite", "url": "https://charmhub.io/cos-lite/"},
                    ],
                },
                {
                    "category": "Contribute",
                    "links": [
                        {"name": "GitHub", "url": "https://github.com/canonical/cos-lite-bundle/"},
                        {"name": "CharmHub", "url": "https://charmhub.io/"},
                    ],
                },
            ]
        }


if __name__ == "__main__":
    main(CosDashboardCharm)
