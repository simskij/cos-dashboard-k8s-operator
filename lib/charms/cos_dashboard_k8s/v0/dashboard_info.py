"""TODO: Add a proper docstring here.

This is a placeholder docstring for this charm library. Docstrings are
presented on Charmhub and updated whenever you push a new version of the
library.

Complete documentation about creating and documenting libraries can be found
in the SDK docs at https://juju.is/docs/sdk/libraries.

See `charmcraft publish-lib` and `charmcraft fetch-lib` for details of how to
share and consume charm libraries. They serve to enhance collaboration
between charmers. Use a charmer's libraries for classes that handle
integration with their charm.

Bear in mind that new revisions of the different major API versions (v0, v1,
v2 etc) are maintained independently.  You can continue to update v0 and v1
after you have pushed v3.

Markdown is supported, following the CommonMark specification.
"""

from ops.framework import BoundEvent, EventBase, EventSource, Object, ObjectEvents
from ops.charm import CharmBase

import logging

LIBID = "45208406413c4910a95babe7910a6ff9"
LIBAPI = 0
LIBPATCH = 1

DEFAULT_RELATION_NAME = "dashboard-info"

logger = logging.getLogger(__name__)

class DashboardEntry:
    name: str
    url: str
    icon: str

class DashboardInfoProvider(Object):

    def __init__(
        self, 
        charm,
        relation_name: str = DEFAULT_RELATION_NAME, 
        entry: DashboardEntry = None
    ):
        super().__init__(charm, relation_name)
        self._charm = charm
        self._relation_name = relation_name
        self._entry = entry

        events = self._charm.on[self._relation_name]
        self.framework.observe(events.relation_joined, self._on_relation_changed)

    def _on_relation_changed(self, event):
        if not self._charm.unit.is_leader():
            return
        
        if not self._entry:
            return
        
        for relation in self._charm.model.relations[self._relation_name]:
            relation.data[relation.app]["name"] = self._entry.name
            relation.data[relation.app]["url"] = self.unit_address
            relation.data[relation.app]["icon"] = self._entry.icon

    @property
    def unit_address(self):
        if self._entry.url:
            return self._entry.url
        
        unit_ip = str(self._charm.model.get_binding(relation).network.bind_address)
        if self._is_valid_unit_address(unit_ip):
            return unit_ip
        
        return socket.getfqdn()




class EntriesChangedEvent(EventBase):
    """Event emitted when dashboard entries change."""

    def __init__(self, handle, apps):
        super().__init__(handle)
        self.apps  = apps

    def snapshot(self):
        """Save dashboard entries information."""
        return {"apps": self.apps}

    def restore(self, snapshot):
        """Restore dashboard entries information."""
        self.apps = snapshot["apps"]


class DashboardInfoEvents(ObjectEvents):
    """Events raised by `DashboardInfoConsumer`"""

    entries_changed = EventSource(EntriesChangedEvent)

class DashboardInfoConsumer(Object):

    on = DashboardInfoEvents()

    def __init__(self, charm: CharmBase, relation_name: str = DEFAULT_RELATION_NAME):
        super().__init__(charm, relation_name)
        self._charm = charm
        self._relation_name = relation_name
        events = self._charm.on[self._relation_name]
        self.framework.observe(events.relation_changed, self._on_relation_changed)
        self.framework.observe(events.relation_joined, self._on_relation_changed)
        self.framework.observe(events.relation_departed, self._on_relation_changed)
        self.framework.observe(events.relation_broken, self._on_relation_changed)

    def _on_relation_changed(self, event):
        
        self.on.entries_changed.emit(apps=self.entries)

    @property
    def entries(self):
        return [
            {
                "name": relation.data[relation.app].get("name", ""),
                "url": relation.data[relation.app].get("url", ""),
                "icon": relation.data[relation.app].get("icon", "") 
            }
            for relation in self._charm.model.relations[self._relation_name]
        ]