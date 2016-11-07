from django import forms
from django.utils.html import format_html
from django.utils.encoding import (
    force_str, force_text, python_2_unicode_compatible,
)
from django.forms.utils import flatatt

class MediaMixin(object):
    pass
    
    class Media:
        css = {'screen':('charsleft-widget/css/charsleft.css',),}
        js = ('charsleft-widget/js/charsleft.js',)
    
class CharsLeftInput(forms.Widget, MediaMixin):
            
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        maxlength = final_attrs.get('maxlength', False)
        if not maxlength:
            return format_html('<textarea{}>\r\n{}</textarea>', flatatt(final_attrs), force_text(value))
        current = force_str(int(maxlength) - len(value))
        html = u"""
            <span class="charsleft charsleft-input">
            <textarea{}>{}</textarea>
            <span><span class="count">{}</span> characters remaining</span>
            <span class="maxlength">{}</span>
            </span>
        """ 
        return format_html(html, flatatt(final_attrs), force_text(value), current, int(maxlength))
