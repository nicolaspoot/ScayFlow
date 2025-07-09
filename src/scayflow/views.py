# src/scayflow/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Cliente, Tramite, Proyecto, Pago
import json
from decimal import Decimal
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

#Vistas para proyectos
@login_required
def proyectos(request):
    return render(request,'proyectos/proyectos.html')

from decimal import Decimal

@login_required
def nuevo_proyecto(request):
    if request.method == 'POST':
        # Crear proyecto
        proyecto = Proyecto.objects.create(
            nombre=request.POST.get('nombre'),
            tipo_proyecto=request.POST.get('tipo_proyecto'),
            cliente_id=request.POST.get('cliente_id'),
            estado='1',
            fecha_inicio=request.POST.get('fecha_inicio'),
            fecha_fin=request.POST.get('fecha_fin') or None,
            descripcion=request.POST.get('descripcion'),
            sector=request.POST.get('sector'),
            costo_base=request.POST.get('costo_base'),
            tarifa_porcentaje=request.POST.get('tarifa_porcentaje'),
            nota=request.POST.get('nota')
        )

        # Crear trámites
        tramites = json.loads(request.POST.get('tramites_json', '[]'))
        for t in tramites:
            fecha_fin_tramite = t.get('fecha_fin', None)
            if not fecha_fin_tramite:
                fecha_fin_tramite = None
            tramite = Tramite.objects.create(
                proyecto=proyecto,
                nombre=t['nombre'],
                descripcion=t['descripcion'],
                costo_base=t['costo_base'],
                tarifa_porcentaje=t['tarifa_porcentaje'],
                duracion_estimada=t['duracion_estimada'],
                tiempo_resolucion=t.get('tiempo_resolucion', ''),
                dependencia=t.get('dependencia', ''),
                responsable_dependencia=t.get('responsable_dependencia', ''),
                estatus=t.get('estatus', ''),
                documentos_requeridos=t.get('documentos_requeridos', ''),
                observaciones=t.get('observaciones', ''),
                fecha_ultima_actualizacion=None,
                fecha_inicio=t.get('fecha_inicio', None),
                fecha_fin=fecha_fin_tramite,
            )
            # Actualiza los totales usando los valores ya generados por SQL
            tramite.refresh_from_db()
            tramite.total_tramite = (
                Decimal(tramite.costo_base or 0) +
                Decimal(tramite.tarifa_monto or 0) +
                Decimal(tramite.iva_monto or 0)
            )
            tramite.save(update_fields=['total_tramite'])

        # Actualiza los totales y utilidad en el proyecto
        proyecto.refresh_from_db()
        proyecto.total = (
            Decimal(proyecto.costo_base or 0) +
            Decimal(proyecto.tarifa_monto or 0) +
            Decimal(proyecto.iva_monto or 0)
        )

        # Cálculo de utilidad_total (puede ser solo la tarifa(s) o según tu fórmula)
        # Ejemplo: suma de tarifa_monto de proyecto y todos los trámites
        utilidad_tramites = sum([
            float(tramite.tarifa_monto or 0)
            for tramite in proyecto.tramites.all()
        ])
        utilidad_proyecto = float(proyecto.tarifa_monto or 0)
        proyecto.utilidad_total = utilidad_proyecto + utilidad_tramites

        proyecto.save(update_fields=['total', 'utilidad_total'])

        return redirect('lista_proyectos')
    else:
        clientes = Cliente.objects.all()
        return render(request, 'proyectos/nuevo_proyecto.html', {'clientes': clientes})
    
@login_required
def lista_proyectos(request):
    return render(request,'proyectos/lista_proyectos.html')
@login_required
def detalles(request):
    return render(request,'proyectos/nuevo_proyecto.html')


#Vistas para clientes
@login_required
def clientes(request):
    return render(request,'clientes/clientes.html')
@login_required
def nuevo_cliente(request):
    if request.method == 'POST':
        Cliente.objects.create(
            nombre=request.POST.get('nombre', ''),
            email=request.POST.get('email', ''),
            telefono=request.POST.get('telefono', ''),
            direccion=request.POST.get('direccion', ''),
            empresa=request.POST.get('empresa', ''),
            persona_contacto=request.POST.get('persona_contacto', ''),
            tipo=request.POST.get('tipo', ''),
            rfc=request.POST.get('rfc', ''),
            notas=request.POST.get('notas', ''),
        )
        return redirect('lista_clientes')  # Ajusta al nombre correcto en tu urls.py
    return render(request, 'clientes/nuevo_cliente.html')
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'clientes/lista_clientes.html', {'clientes': clientes})
@login_required
def editar_cliente(request):
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')
        cliente = get_object_or_404(Cliente, cliente_id=cliente_id)

        # Actualiza los campos
        cliente.nombre = request.POST.get('nombre', cliente.nombre)
        cliente.email = request.POST.get('email', cliente.email)
        cliente.telefono = request.POST.get('telefono', cliente.telefono)
        cliente.empresa = request.POST.get('empresa', cliente.empresa)
        cliente.tipo = request.POST.get('tipo', cliente.tipo)
        cliente.rfc = request.POST.get('rfc', cliente.rfc)
        # Si tienes más campos, agrégalos aquí

        try:
            cliente.save()
            messages.success(request, "Cliente actualizado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al actualizar: {e}")

        # Redirecciona de vuelta a la lista de clientes
        return redirect('lista_clientes')
    else:
        messages.error(request, "Acceso no permitido.")
        return redirect('lista_clientes')

#Vistas para tramites
#def tramites(request):
    #return render(request,'tramites/tramites.html')
@login_required
def nuevo_tramite(request):
    return render(request,'tramites/nuevo_tramite.html')
@login_required
def lista_tramites(request):
    return render(request,'tramites/lista_tramites.html')

#Vistas para pagos
@login_required
def pagos(request):
    return render(request,'pagos/pagos.html')
@login_required
def nuevo_pago(request):
    proyectos = Proyecto.objects.all()
    proyecto_id = request.GET.get('proyecto_id') or request.POST.get('proyecto_id')
    proyecto = Proyecto.objects.filter(pk=proyecto_id).first() if proyecto_id else None
    tramites = proyecto.tramites.all() if proyecto else []

    error_msg = None

    if request.method == 'POST' and proyecto:
        monto = Decimal(request.POST.get('monto'))
        fecha = request.POST.get('fecha')
        metodo_pago = request.POST.get('metodo_pago')
        comprobante = request.FILES.get('comprobante') or request.POST.get('comprobante')
        nota = request.POST.get('nota')
        pago_tipo = request.POST.get('pago_tipo')
        tramite_id = request.POST.get('tramite_id')
        tramite = Tramite.objects.get(pk=tramite_id) if (pago_tipo == 'tramite' and tramite_id) else None

        # Validación: que no pague más de lo pendiente
        if pago_tipo == 'proyecto':
            pendiente = proyecto.saldo_pendiente
            if monto > pendiente:
                error_msg = f"No puedes abonar más de lo pendiente (${pendiente:.2f}) en el proyecto."
        elif pago_tipo == 'tramite' and tramite:
            pendiente = tramite.saldo_pendiente
            if monto > pendiente:
                error_msg = f"No puedes abonar más de lo pendiente (${pendiente:.2f}) en el trámite seleccionado."

        # Responde error si es AJAX
        if error_msg and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})

        if not error_msg:
            Pago.objects.create(
                proyecto=proyecto if pago_tipo == 'proyecto' else None,
                tramite=tramite,
                monto=monto,
                fecha=fecha,
                metodo_pago=metodo_pago,
                comprobante=comprobante,
                notas=nota
            )

            # Refresca y recalcula los datos necesarios
            proyecto.refresh_from_db()
            tramites = proyecto.tramites.all()
            total_pagado = proyecto.total_pagado
            saldo = proyecto.saldo_pendiente
            porcentaje_pagado = porcentaje_pendiente = 0
            iva = getattr(proyecto, 'iva', 0) if proyecto else 0
            if proyecto.total:
                porcentaje_pagado = round(Decimal(proyecto.total_pagado) / Decimal(proyecto.total) * 100, 1) if proyecto.total > 0 else 0
                porcentaje_pendiente = round(Decimal(proyecto.saldo_pendiente) / Decimal(proyecto.total) * 100, 1) if proyecto.total > 0 else 0

            total_tramites = sum([t.total_tramite for t in tramites]) if tramites else 0
            total_pagado_tramites = sum([t.total_pagado for t in tramites]) if tramites else 0
            total_pendiente_tramites = sum([t.saldo_pendiente for t in tramites]) if tramites else 0
            n_tramites = len(tramites)
            porc_pagado = round((Decimal(total_pagado_tramites) / Decimal(total_tramites) * 100), 1) if total_tramites else 0
            porc_pendiente = round((Decimal(total_pendiente_tramites) / Decimal(total_tramites) * 100), 1) if total_tramites else 0

            # Si es AJAX, renderiza sólo el bloque parcial y responde
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                html = render_to_string('pagos/proyecto_info.html', {
                    'proyecto': proyecto,
                    'tramites': tramites,
                    'total_pagado': total_pagado,
                    'saldo': saldo,
                    'iva': iva,
                    'porcentaje_pagado': porcentaje_pagado,
                    'porcentaje_pendiente': porcentaje_pendiente,
                    'total_tramites': total_tramites,
                    'total_pagado_tramites': total_pagado_tramites,
                    'total_pendiente_tramites': total_pendiente_tramites,
                    'n_tramites': n_tramites,
                    'porc_pagado': porc_pagado,
                    'porc_pendiente': porc_pendiente,
                }, request=request)
                return JsonResponse({'success': True, 'html': html})

            # Si no es AJAX, redirige normal
            return redirect('nuevo_pago')

    total_pagado = proyecto.total_pagado if proyecto else 0
    saldo = proyecto.saldo_pendiente if proyecto else 0

    # ==== RESUMEN PROYECTO ====
    porcentaje_pagado = porcentaje_pendiente = 0
    iva = getattr(proyecto, 'iva', 0) if proyecto else 0
    if proyecto and proyecto.total:
        porcentaje_pagado = round(Decimal(proyecto.total_pagado) / Decimal(proyecto.total) * 100, 1) if proyecto.total > 0 else 0
        porcentaje_pendiente = round(Decimal(proyecto.saldo_pendiente) / Decimal(proyecto.total) * 100, 1) if proyecto.total > 0 else 0

    # ==== RESUMEN TRÁMITES ====
    total_tramites = sum([t.total_tramite for t in tramites]) if tramites else 0
    total_pagado_tramites = sum([t.total_pagado for t in tramites]) if tramites else 0
    total_pendiente_tramites = sum([t.saldo_pendiente for t in tramites]) if tramites else 0
    n_tramites = len(tramites)
    porc_pagado = round((Decimal(total_pagado_tramites) / Decimal(total_tramites) * 100), 1) if total_tramites else 0
    porc_pendiente = round((Decimal(total_pendiente_tramites) / Decimal(total_tramites) * 100), 1) if total_tramites else 0

    return render(request, 'pagos/nuevo_pago.html', {
        'proyectos': proyectos,
        'proyecto': proyecto,
        'tramites': tramites,
        'total_pagado': total_pagado,
        'saldo': saldo,
        'error_msg': error_msg,
        'iva': iva,
        # Para sección de proyecto
        'porcentaje_pagado': porcentaje_pagado,
        'porcentaje_pendiente': porcentaje_pendiente,
        # Para sección de trámites
        'total_tramites': total_tramites,
        'total_pagado_tramites': total_pagado_tramites,
        'total_pendiente_tramites': total_pendiente_tramites,
        'n_tramites': n_tramites,
        'porc_pagado': porc_pagado,
        'porc_pendiente': porc_pendiente,
    })