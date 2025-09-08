from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    """Render HTML to PDF using xhtml2pdf"""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    
    # Create PDF
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def generate_pdf_response(template_name, context, filename):
    """Generate PDF response with proper filename"""
    pdf = render_to_pdf(template_name, context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return HttpResponse("Error generating PDF", status=500)


def sum_attr(queryset, attr):
    """Sum a specific attribute from a queryset"""
    return sum(getattr(item, attr) for item in queryset)

# Add to your view context
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    # ...
    context['delivery_items_total'] = sum_attr(self.object.items.all(), 'total_price')
    return context