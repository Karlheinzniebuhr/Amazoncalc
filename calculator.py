import os
import urllib, urllib2

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

import sys
sys.path.insert(0,'libs')

from bs4 import BeautifulSoup
import re

from amazon.api import AmazonAPI

import json
import config

amazon = AmazonAPI(config.AWS_ACCESS_KEY_ID, config.AWS_SECRET_ACCESS_KEY, config.AWS_ASSOCIATE_TAG)

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]


# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):

        # Try to get Dolar Price from Marce's Dolarpy API
        try:
            js = json.load(urllib2.urlopen("https://dolar.melizeche.com/api/1.0/"))

            # Get average cotizacion
            avg = 0
            n = 0
            for key, value in js['dolarpy'].iteritems():
                if value['venta'] > 0:
                    n += 1
                    avg += value['venta']
            cotizacion = int(avg/n)
        except:
            e = sys.exc_info()[0]
            print str(e) + ' Dolar API error'
            cotizacion = 5000

        template_values = {
            'cotizacion': cotizacion,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
# [END main_page]

class Result(webapp2.RequestHandler):

    def get(self):

        def extract_number(id,string):
            s = str(string)
            print 'string to extract number from: ' + s

            try:
                n = re.findall(r"[-+]?\d*\.\d+|\d+", s)[0]
                return float(n)
            except:
                e = sys.exc_info()[0]
                print str(e) + ' Extract_number error on ' + id
                return 0

        def getasin(url):
            asin = re.findall(r"(?<=\/dp\/)(.*)", url)[0]
            if not asin > '':
                asin = re.findall(r"(?<=\/product\/)(.*)", url)[0]
            asin = asin[:10]
            if not len(asin) == 10:
                raise ValueError('invalid ASIN')
            return asin

        def test_getasin():
            urls = ['https://www.amazon.com/Nintendo-Switch-Gray-Joy-Con/dp/B01LTHP2ZK?tag=kasbl023-20']
            for url in urls:
                getasin(url)


        url = self.request.GET['url']
        precio_envio = extract_number('precio envio',self.request.GET['precio_envio'])
        cotizacion = int(extract_number('cotizacion',self.request.GET['cotizacion']))

        # Get item ID from URL
        itemasin = getasin(url)

        # find product data with the Amazon api
        print "searching ASIN: " + str(itemasin)
        try:
            product = amazon.lookup(ItemId=itemasin, ResponseGroup='Offers, ItemAttributes', Condition='All', MerchantId='All')
            precio = extract_number('precio',product.price_and_currency[0])
            peso = extract_number('peso',product.get_attribute('PackageDimensions.Weight'))

            precio_gs = precio * cotizacion
            peso_g = peso * 0.01 * 453.492

            precio_envio_gs = (peso_g/1000) * precio_envio * cotizacion
            precio_total = precio_gs + precio_envio_gs
            precio_up = precio_total * 1.3
            precio_up = int(round(precio_up,-3))

            template_values = {
                'precio': precio,
                'url': url,
                'precio_producto': str('{0:,}'.format(precio)),
                'precio_gs': str('{0:,}'.format(int(precio_gs))),
                'peso_envio': str('{0:,}'.format(int(peso_g))),
                'cotizacion': cotizacion,
                'precio_envio': str('{0:,}'.format(int(precio_envio))),
                'precio_envio_gs': str('{0:,}'.format(int(precio_envio_gs))),
                'precio_total': str('{0:,}'.format(int(precio_total))),
                'precio_up': str('{0:,}'.format(int(precio_up))),
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
        except:
            e = sys.exc_info()
            e2 = sys.exc_info()[0]
            print str(e)
            template_values = {
                'error': e,
                'error_summary': e2,
            }
            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))


# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/result', Result),
], debug=True)
# [END app]
