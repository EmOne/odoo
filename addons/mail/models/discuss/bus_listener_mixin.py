# Part of Odoo. See LICENSE file for full copyright and licensing details.

from markupsafe import Markup

from odoo import models


class BusListenerMixin(models.AbstractModel):
    _inherit = "bus.listener.mixin"

    def _bus_send_transient_message(self, channel, content):
        """Posts a fake message in the given ``channel``, only visible for ``self`` listeners."""
        self._bus_send(
            "discuss.channel/transient_message",
            {
                "body": Markup("<span class='o_mail_notification'>%s</span>") % content,
                "channel_id": channel.id,
            },
        )
