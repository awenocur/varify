from django.http import QueryDict
from serrano.resources.exporter import ExporterResource
from avocado.models import DataView

class VcfExporterResource(ExporterResource):

    def get_view(self, request, attrs=None):
        # Just return the variant ID, we will do the lookup ourselves. It's
        # easier to access the data in the exporter than to try to hard code
        # all the concept IDs here.
        return DataView(json='{"columns": [31]}')

    def is_not_found(self, request, response, *args, **kwargs):
        return super(VcfExporterResource, self).is_not_found(
            request, response, 'vcf', **kwargs)

    def get(self, request, **kwargs):
        return super(VcfExporterResource, self).get(
            request, 'vcf', **kwargs)

    def post(self, request, **kwargs):
    #TODO: remove following hack once Serrano ceases to require data attr
        #the following is a hack, to prevent Serrano from crashing
        request.data = QueryDict('')
        return super(VcfExporterResource, self).post(
            request, 'vcf', **kwargs)

    def dispatch(self, *args, **kwargs):
        return super(VcfExporterResource, self).dispatch(*args, **kwargs)

    supported_accept_types = ('*/*',)
    supported_content_types = ('text/plain',)
    attrs = ''