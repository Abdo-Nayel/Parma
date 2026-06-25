from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .permissions import require_module


@login_required
def delete_confirm(request, model, pk, blockers_fn, redirect_name, module, object_label=None, page_title='تأكيد الحذف'):
    @require_module(module, 'delete')
    def _inner(req):
        obj = get_object_or_404(model, pk=pk)
        blockers = blockers_fn(obj)
        label = object_label(obj) if object_label else str(obj)

        if req.method == 'POST':
            if blockers:
                messages.error(req, 'لا يمكن الحذف: ' + '، '.join(blockers))
            else:
                obj.delete()
                messages.success(req, f'تم حذف «{label}»')
            return redirect(redirect_name)

        return render(req, 'partials/delete_confirm.html', {
            'page_title': page_title,
            'object': obj,
            'object_label': label,
            'blockers': blockers,
            'cancel_url_name': redirect_name,
        })

    return _inner(request)
