from django.core.exceptions import PermissionDenied

from .models import Membership


ROLE_RANK = {
    Membership.Role.VIEWER: 10,
    Membership.Role.BILLING: 20,
    Membership.Role.MAINTAINER: 30,
    Membership.Role.OWNER: 40,
}


def require_membership(user, organization, minimum_role=Membership.Role.VIEWER):
    membership = Membership.objects.filter(user=user, organization=organization).first()
    if not membership or ROLE_RANK[membership.role] < ROLE_RANK[minimum_role]:
        raise PermissionDenied
    return membership
