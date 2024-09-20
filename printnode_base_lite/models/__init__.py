# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

# This is important to load res.company first, as new attributes from this model used
# in the other models
from . import res_company

from . import printnode_account
from . import printnode_printer
from . import printnode_computer
from . import printnode_printjob
from . import printnode_action_button
from . import printnode_scales
from . import printnode_scenario 
from . import printnode_report
from . import printnode_rule
from . import shipping_label
from . import printnode_workstation
from . import printnode_base

from . import res_config_settings
from . import res_users
from . import ir_http
from . import stock_picking
