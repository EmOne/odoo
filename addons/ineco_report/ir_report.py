# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 INECO PARNTERSHIP LIMITED (http://openerp.tititab.com) 
# All Right Reserved
#
# Author : Tititab Srisookco (thitithup@gmail.com)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import openerp

from openerp.osv import osv, fields, orm
from openerp import netsvc
from ineco_report import InecoParser
from openerp.report.report_sxw import rml_parse

def register_report(name, model, tmpl_path, parser=rml_parse):
    "Register the report into the services"
    name = 'report.%s' % name
    if netsvc.Service._services.get(name, False):
        service = netsvc.Service._services[name]
        if isinstance(service, InecoParser):
            #already instantiated properly, skip it
            return
        if hasattr(service, 'parser'):
            parser = service.parser
        del netsvc.Service._services[name]
    InecoParser(name, model, tmpl_path, parser=parser)

class ir_actions_report_xml(orm.Model):

    _inherit = 'ir.actions.report.xml'
    _columns = {
        'jasper_url': fields.char('Jasper Server URL', size=254),
        'jasper_report_path': fields.char('Jaser Server Report Path', size=254),
        'jasper_username': fields.char('User Name', size=20),
        'jasper_password': fields.char('Password', size=20),
        'criteria_field': fields.char('Criteria Field', size=100),
        'parameter_name': fields.char('Jasper Parameter Name', size=100),
        'stamp_ids': fields.one2many('ir.report.stamp','report_id', 'Stamper'),
        'report_type': fields.selection([('qweb-pdf', 'PDF'),
                    ('qweb-html', 'HTML'),
                    ('controller', 'Controller'),
                    ('pdf', 'RML pdf (deprecated)'),
                    ('sxw', 'RML sxw (deprecated)'),
                    ('webkit', 'Webkit (deprecated)'),
                    ('ineco', 'INECO'),
                    ], 'Report Type', required=True, help="HTML will open the report directly in your browser, PDF will use wkhtmltopdf to render the HTML into a PDF file and let you download it, Controller allows you to define the url of a custom controller outputting any kind of report."),
    }
    
    _defaults = {
        'jasper_url': 'http://localhost:8080/jasperserver/services/repository?wsdl',
    }
    
    def _lookup_report(self, cr, name):
        """
        Look up a report definition.
        """
        import operator
        import os
        opj = os.path.join

        # First lookup in the deprecated place, because if the report definition
        # has not been updated, it is more likely the correct definition is there.
        # Only reports with custom parser specified in Python are still there.
        if 'report.' + name in openerp.report.interface.report_int._reports:
            new_report = openerp.report.interface.report_int._reports['report.' + name]
            if not isinstance(new_report, InecoParser):
                new_report = None
        else:
            cr.execute("SELECT * FROM ir_act_report_xml WHERE report_name=%s and report_type=%s", (name, 'ineco'))
            r = cr.dictfetchone()
            if r:
                if r['parser']:
                    parser = operator.attrgetter(r['parser'])(openerp.addons)
                    kwargs = { 'parser': parser }
                else:
                    kwargs = {}

                new_report = InecoParser('report.'+r['report_name'],
                    r['model'], opj('addons',r['report_rml'] or '/'),
                    header=r['header'], register=False, **kwargs)
            else:
                new_report = None

        if new_report:
            return new_report
        else:
            return super(ir_actions_report_xml, self)._lookup_report(cr, name)

    def add_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        report = self.pool.get('ir.actions.report.xml').browse(cr, uid, ids, context=context)
        report_ids = self.pool.get('ir.values').search(cr, uid, [('value','=',report.type+','+str(ids[0]))])
        if not report_ids:
            res = self.pool.get('ir.model.data').ir_set(cr, uid, 'action', 'client_print_multi', 
                report.report_name, [report.model], 
                'ir.actions.report.xml,%d' % ids[0], isobject=True)
        else:
            raise osv.except_osv('Error!', "Can not add duplicate button!")
        return True

    def remove_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        report = self.pool.get('ir.actions.report.xml').browse(cr, uid, ids, context=context)

        report_ids = self.pool.get('ir.values').search(cr, uid, [('value','=',report.type+','+str(ids[0]))])
        for report_id in report_ids:
            self.pool.get('ir.values').unlink(cr, uid, report_id)
        return True
    
class ir_report_stamp(osv.osv):
    _name = 'ir.report.stamp'
    _description = 'PDF Stampper'
    _columns = {
        'name': fields.char('Description',size=64),
        'seq': fields.integer('Sequence'),
        'type': fields.selection([
            ('original','Original'),
            ('original_thai','Original - Thai'),
            ('copy','Copy'), 
            ('copy_thai','Copy - Thai')], 'Type'),
        'position_x': fields.integer('X'),
        'position_y': fields.integer('Y'),
        'size_width': fields.integer('Width'),
        'size_height': fields.integer('Height'),
        'report_id': fields.many2one('ir.actions.report.xml','Reports'),
    }
    _defaults = {
        'type': 'original',
        'name': '...',
        'seq': 1,
        'position_x': 450,
        'position_y': 750,
        'size_width': 140,
        'size_height': 72,
    }
    _order = 'report_id, seq'
