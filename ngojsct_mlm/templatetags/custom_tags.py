from django import template
from ..models import CustomUser

register=template.Library()

@register.simple_tag
def latest_id():
    obj= CustomUser.objects.latest('id')
    # for i in obj:
    #     id=i.id
    print(obj.memberID)
    return obj.memberID



# register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')