from django import template

register = template.Library()

@register.filter
def get_community_name(communities, community_id):
    for value, name in communities:
        if str(value) == str(community_id):
            return name
    return ''
