# src/scayflow/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


#Vistas para proyectos
@login_required
def proyectos(request):
    return render(request,'proyectos/proyectos.html')

@login_required
def nuevo_proyecto(request):
    return render(request,'proyectos/nuevo_proyecto.html')
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
    return render(request,'clientes/nuevo_cliente.html')
@login_required
def lista_clientes(request):
    return render(request,'clientes/lista_clientes.html')

#Vistas para tramites
#def tramites(request):
    #return render(request,'tramites/tramites.html')
@login_required
def nuevo_tramite(request):
    return render(request,'tramites/nuevo_tramite.html')
@login_required
def lista_tramites(request):
    return render(request,'tramites/lista_tramites.html')