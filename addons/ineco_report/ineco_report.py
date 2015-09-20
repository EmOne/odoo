# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 INECO PARTNERSHIP LIMITED (http://openerp.tititab.com) 
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

# Date             ID         Message
# 1-1-2012         POP-001    Add Class Ineco.Report.Config

import commands
import os
import openerp.report
import tempfile
import time
from mako.template import Template
from mako import exceptions
#import netsvc
from openerp import pooler
#import openerp.pooler
from openerp.report.report_sxw import *
#import addons
from openerp.tools.translate import _
from openerp.osv.osv import except_osv
from openerp.osv import fields,osv
import jasperclient
import base64
from pyPdf import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class InecoParser(report_sxw):
    """Custom class that use webkit to render HTML reports
       Code partially taken from report openoffice. Thanks guys :)
    """

    def __init__(self, name, table, rml=False, parser=rml_parse,
        header=True, store=False, register=True):
        self.localcontext = {}
        report_sxw.__init__(self, name, table, rml, parser,
            header, store, register=register)
    
    def __init__old(self, name, table, rml=False, parser=False, 
        header=True, store=False):
        self.parser_instance = False
        self.localcontext={}
        report_sxw.__init__(self, name, table, rml, parser, 
            header, store)

    def generate_pdf(self, cr, uid, ids, data, report_xml):
        field_in = report_xml.criteria_field
        url = report_xml.jasper_url
        user = report_xml.jasper_username
        password = report_xml.jasper_password
        report_path = report_xml.jasper_report_path
        parameter = report_xml.parameter_name
        format = 'pdf'
        report_param = {}
        user_obj = self.pool.get('res.users').browse(cr, uid, uid)
        user_print_name = user_obj.name
        if field_in and url and user and password and report_path:
            criteries = field_in + ' in '+ str(tuple( sorted(ids)))
            criteries = criteries.replace(',)',')')
            if parameter:
                report_param[parameter] = criteries
                report_param['user_print_name'] = user_print_name
            j = jasperclient.JasperClient(url,user,password)
            a = j.runReport(report_path,format, report_param) # {'pick_ids': criteries})
            buf = StringIO()
            buf.write(a['data'])
            pdf = buf.getvalue()
            if report_xml.stamp_ids:
                input_buff = buf.getvalue()
                buf.close()            
                output = PdfFileWriter()
                original = os.path.join(os.getcwd(),'openerp/addons/ineco_report/images/original.png')
                original_thai = os.path.join(os.getcwd(),'openerp/addons/ineco_report/images/original_thai.png')
                copy = os.path.join(os.getcwd(),'openerp/addons/ineco_report/images/copy.png')
                copy_thai = os.path.join(os.getcwd(),'openerp/addons/ineco_report/images/copy_thai.png')
                for stamp in report_xml.stamp_ids:
                    input_IO = StringIO()
                    input_IO.write(a['data'])
                    input = PdfFileReader(input_IO)
                    if stamp.type == 'original':
                        imgPath = original
                    elif stamp.type == 'original_thai':
                        imgPath = original_thai
                    elif stamp.type == 'copy':
                        imgPath = copy
                    elif stamp.type == 'copy_thai':
                        imgPath = copy_thai
                    else:
                        imgPath = original
                    imgTemp = StringIO()
                    imgDoc = canvas.Canvas(imgTemp)
                    imgDoc.drawImage(imgPath, 
                        stamp.position_x or 450, 
                        stamp.position_y or 700, 
                        stamp.size_width or 144, 
                        stamp.size_height or 72, 
                        [255,255,255,255,255,255]) #Transparent
                    imgDoc.save()       
                    numPages = input.getNumPages()    
                    for i in range(0, numPages): 
                        pageNew = input.getPage(i)
                        overlay = PdfFileReader(StringIO(imgTemp.getvalue())).getPage(0)
                        pageNew.mergePage(overlay)
                        output.addPage(pageNew)
                buf = StringIO()
                output.write(buf)
                pdf = buf.getvalue()
        else:
            raise osv.except_osv(_('Warning !'), _('Please fill data in URL, Username, Password, Report Path and Criteria.'))

        return pdf    

    # override needed to keep the attachments' storing procedure
    def create_single_pdf(self, cursor, uid, ids, data, report_xml, context=None):
        """generate the PDF"""
        
        if context is None:
            context={}

        if report_xml.report_type != 'ineco':
            return super(InecoParser,self).create_single_pdf(cursor, uid, ids, data, report_xml, context=context)

        self.parser_instance = self.parser(
                                            cursor,
                                            uid,
                                            self.name2,
                                            context=context
                                        )

        self.pool = pooler.get_pool(cursor.dbname)
        objs = self.getObjects(cursor, uid, ids, context)
        self.parser_instance.set_context(objs, data, ids, report_xml.report_type)

        pdf = self.generate_pdf(cursor, uid, ids, data, report_xml)
        return (pdf, 'pdf')


    def create(self, cursor, uid, ids, data, context=None):
        """We override the create function in order to handle generator
           Code taken from report openoffice. Thanks guys :) """
        pool = pooler.get_pool(cursor.dbname)
        ir_obj = pool.get('ir.actions.report.xml')
        report_xml_ids = ir_obj.search(cursor, uid,
                [('report_name', '=', self.name[7:])], context=context)
        if report_xml_ids:
            
            report_xml = ir_obj.browse(
                                        cursor, 
                                        uid, 
                                        report_xml_ids[0], 
                                        context=context
                                    )
            report_xml.report_rml = None
            report_xml.report_rml_content = None
            report_xml.report_sxw_content_data = None
            report_rml.report_sxw_content = None
            report_rml.report_sxw = None
        else:
            return super(InecoParser, self).create(cursor, uid, ids, data, context)
        if report_xml.report_type != 'ineco' :
            return super(InecoParser, self).create(cursor, uid, ids, data, context)
        result = self.create_source_pdf(cursor, uid, ids, data, report_xml, context)
        if not result:
            return (False,False)
        return result

#POP-001
class ineco_report_config(osv.osv):
    
    _name = "ineco.report.config"
    _description = "Ineco Report Configuration"
    _columns = {
        'name': fields.char('Name', size=100),
        'report_id': fields.char('Report ID', size=100),
        'description': fields.char('Description',size=100),
        'type': fields.char('Report Type', size=50),
        'host': fields.char('Jasper Server Host', size=100),
        'report_user': fields.char('Jasper Uer Name', size=20),
        'report_password': fields.char('Jasper Password', size=20),
        'active': fields.boolean('Active')
    }
    _defaults = {
        'active': True,
        'host': 'localhost',
        'report_user': 'jasperadmin',
        'report_password': 'jasperadmin'
    }
    _order = 'name'
    
ineco_report_config()
