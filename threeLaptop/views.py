import random
import math
import requests as req

from django.middleware import csrf
from django.views import View
from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import logout, login, authenticate, get_user_model
from django.contrib.auth.models import Group
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from goods.models import Barang, SemuaBrand
from users.forms import RegisterForm
from users.models import Subscribe
from users.token import getTokenUser, getIdTransaksi
from address.api_rajaongkir import cekTarif, template as templateRajaOngkir
from transaksi.xendit import makeInvoice
from transaksi.models import Transaksi

class Index(View):
    template_name = 'index.html'
    context = {
        
    }

    def get(self, request, *args, **kwargs):
        jumlahBarang = Barang.objects.all()
        page = 1
        if 'pagination' in request.GET:
            if int(request.GET['pagination']) > 1:
                start   = (int(request.GET['pagination']) - 1) * 9
                end     = start * 2
                barangAll = Barang.objects.all().order_by('-id')[start:end]
                page = int(request.GET['pagination'])
            else:
                barangAll = Barang.objects.all().order_by('-id')
        else:
            barangAll = Barang.objects.all().order_by('-id')

        self.context['pagination'] = math.ceil(len(jumlahBarang) / 9)
        paginationNumber = [page, page + 1, page + 2]
        self.context['paginationNumber'] = paginationNumber

        barangLane = [[], []]
        for barang in barangAll:
            if len(barangLane[1]) == 9:
                break
            barangLane[1].append(barang)

        self.context['allBrand'] = SemuaBrand.objects.all()
        self.context['barangLane'] = barangLane
        self.context['registerForm'] = RegisterForm(use_required_attribute=False)
        self.context['staff'] = Group.objects.get(name='staff')
        self.context['url'] = '/'
        
        if 'search' in request.GET:
            barang = Barang.objects.filter(nama__icontains = request.GET['search'])
            # print(barang)
            page = 1
            barangAll = barang
            if 'pagination' in request.GET:
                if int(request.GET['pagination']) > 1:
                    start   = (int(request.GET['pagination']) - 1) * 9
                    end     = start * 2
                    barangAll = barang[start:end]
                    page = int(request.GET['pagination'])

            self.context['pagination'] = int(math.ceil(len(barangAll) / 9))
            paginationNumber = [page, page + 1, page + 2]
            print(self.context['pagination'])
            self.context['paginationNumber'] = paginationNumber

            barangLane = [[], []]
            if len(barangAll) < 9:
                for brng in barangAll:
                    barangLane[1].append(brng)
            else:
                for brng in barangAll:
                    if len(barangLane[1]) == 9:
                        break
                    barangLane[1].append(brng)
                    
            self.context['barangLane'] = barangLane
            self.context['url'] = "/ajax/search?keyword=" + request.GET['search']
            return render(self.request, self.template_name, self.context)
        
        if request.is_ajax():
            if 'pagination' in request.GET:
                self.template_name = 'listBarang.html'

        return render(request, self.template_name, self.context)


class Ajax(View):
    action = ''
    context = {

    }

    def post(self, request):
        if request.is_ajax():
            if self.action == 'login':
                try:
                    inputUsername = request.POST['username']
                    inputPassword = request.POST['password']
                    print(inputPassword, inputUsername)
                    user = authenticate(request, username=inputUsername, password=inputPassword)
                    if user != '':
                        login(request, user)
                    if request.user.profile == "":
                        self.context['profile_user'] = '/static/asset/images/icon/user.png'
                    else:
                        self.context['profile_user'] = request.user.profile
                    
                    self.context['staff'] = Group.objects.get(name='staff')
                    if 'from' in request.POST:
                        return render(self.request, 'user.html', self.context)
                    else:
                        return render(self.request, 'user.html', self.context)
                except:
                    return JsonResponse({'success': 'false'})

            if self.action == 'register':
                form = RegisterForm(request.POST, request.FILES or None)
                if form.is_valid():
                    token = getTokenUser()
                    form.save()
                    pembeli = Group.objects.get(name='pembeli')
                    user = get_user_model().objects.get(username = request.POST['username'])
                    user.is_active = False
                    user.token = token
                    user.groups.add(pembeli)
                    user.set_password(form.cleaned_data['password'])
                    user.save()

                    email_context = {
                        'token': token,
                        'username': user.username,
                        'email': user.email,
                        'fullName': user.fullname,
                        'url': 'http://127.0.0.1:8000/user/activate/' + str(token)
                    }
                    html = render_to_string('email/register.html', email_context)
                    msg = EmailMessage(
                        'Selamat datang di Three Laptop',
                        html,
                        'jusles363@gmail.com',
                        [request.POST['email']]
                    )
                    msg.content_subtype = 'html'
                    msg.send()

                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False})

            if self.action == 'saveTransaksi':
                transaksi = Transaksi(
                    id_transaksi = str(request.POST['id_transaksi']),
                    barang = request.POST['barang'],
                    harga = request.POST['harga'],
                    detailHarga = request.POST['detailHarga'],
                    alamat = request.POST['userAlamat'],
                    pembeli = request.user, 
                    ekspedisi = request.POST['ekspedisi'],
                )
                transaksi.save()
                user = get_user_model().objects.get(username = request.user.username)
                user.transaksi = str(request.POST['id_transaksi']) if user.transaksi == None or user.transaksi == '' else user.transaksi + ', ' + str(request.POST['id_transaksi'])
                user.save()
                return JsonResponse({'success': 'true'})

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            if self.action == 'logout':
                logout(request)
                return JsonResponse({'success': True})

            if self.action == 'csrf':
                return JsonResponse({'csrf': csrf.get_token(request)})

            if self.action == 'cart':
                if 'barang' in request.COOKIES and request.COOKIES['barang'] != "":
                    listBarang = request.COOKIES['barang'].split(', ')

                    data = []
                    # listCookie = ''
                    for barang in listBarang:
                        listBarang = barang.split(' : ')
                        barang = Barang.objects.get(nama=listBarang[0])

                        if listBarang[1] == 'random':
                            barangWarna = barang.warna.split(', ')
                            length = len(barangWarna)
                            randomNumber = random.randint(1, length) - 1
                            listBarang[1] = barangWarna[randomNumber]

                        data.append({
                            'nama': listBarang[0],
                            'warna': listBarang[1],
                            'jumlah': listBarang[2],
                            'cover': barang.image1,
                            'harga': barang.harga,
                            'slugify': barang.slugifyBarang,
                            'hargaTotal': int(listBarang[2]) * int(barang.harga)
                        })
                        # cookie = "{} : {} : {}".format(listBarang[0], listBarang[1], listBarang[2])
                        # if listCookie == '':
                        #     listCookie += cookie
                        # else:
                        #     listCookie += ', ' + cookie

                    totalHarga = 0
                    for harga in data:
                        totalHarga += harga['hargaTotal']

                    self.context = {
                        'barangCart': data,
                        'totalHarga': totalHarga,
                        'success': True
                    }
                return render(self.request, 'cart.html', self.context)
            
            if self.action == 'get_kabupaten':
                idProvinsi = self.request.GET['id_provinsi']
                kabupaten = req.get("http://dev.farizdotid.com/api/daerahindonesia/provinsi/" + idProvinsi + "/kabupaten").json()
                self.context = {
                    'listKabupaten': kabupaten['kabupatens']
                }
                return render(self.request, 'address/listKabupaten.html', self.context)
            
            if self.action == 'get_kecamatan':
                idKecamatan = self.request.GET['id_kabupaten']
                kecamatan = req.get("http://dev.farizdotid.com/api/daerahindonesia/provinsi/kabupaten/" + idKecamatan + "/kecamatan").json()
                self.context = {
                    'listKecamatan': kecamatan['kecamatans']
                }
                return render(self.request, 'address/listKecamatan.html', self.context)
        
            if self.action == 'search':
                barang = Barang.objects.filter(nama__icontains = request.GET['keyword'])
                page = 1
                barangAll = barang
                if 'pagination' in request.GET:
                    if int(request.GET['pagination']) > 1:
                        start   = (int(request.GET['pagination']) - 1) * 9
                        end     = start * 2
                        barangAll = barang[start:end]
                        page = int(request.GET['pagination'])

                self.context['pagination'] = math.ceil(len(barangAll) / 9)
                paginationNumber = [page, page + 1, page + 2]
                self.context['paginationNumber'] = paginationNumber

                barangLane = [[], []]
                if len(barangAll) < 9:
                    for brng in barangAll:
                        barangLane[1].append(brng)
                else:
                    for brng in barangAll:
                        if len(barangLane[1]) == 9:
                            break
                        barangLane[1].append(brng)
                        
                self.context['barangLane'] = barangLane
                self.context['url'] = "/ajax/search?keyword=" + request.GET['keyword']
                return render(self.request, 'listBarang.html', self.context)
            
            if self.action == 'profile':
                if request.user.profile == "":
                    self.context['profile_user'] = '/static/asset/images/icon/user.png'
                else:
                    self.context['profile_user'] = request.user.profile
                return render(self.request, 'user/profile.html', self.context)
            
            if self.action == 'ongkir':
                kontak = {
                    'email': request.GET['email'],
                    'nomerHp': request.GET['nomerHp'],
                }
                alamat = {
                    'label': request.GET['label'],
                    'namaLengkap': request.GET['namaLengkap'],
                    'provinsi': request.GET['provinsi'],
                    'kabupaten': request.GET['kabupaten'],
                    'kabupatenAsli': request.GET['kabupatenAsli'],
                    'kecamatan': request.GET['kecamatan'],
                    'kodePos': request.GET['kodePos'],
                    'informasiTambahan': request.GET['informasiTambahan'],
                    'simpan': request.GET['simpan']
                }
                
                id_transaksi = getIdTransaksi()

                saveAlamat = "Label: {} | Nama Lengkap: {} | Provinsi: {} | Kabupaten: {}/{} | Kecamatan: {} | Kode Pos: {} | Informasi Tambahan: {}".format(
                    alamat['label'], alamat['namaLengkap'], alamat['provinsi'], alamat['kabupaten'], alamat['kabupatenAsli'], alamat['kecamatan'], alamat['kodePos'], alamat['informasiTambahan']
                )
                if alamat['simpan'] == 'true':
                    user = get_user_model().objects.get(username = request.user.username)
                    user.alamat = saveAlamat
                    user.save()
                
                kotaAsal = 'Banyuwangi'
                kotaTujuan = alamat['kabupaten']
                berat = '2000'
                ekspedisi = ['tiki', 'jne', 'pos']
                dataOngkirTiki  = cekTarif(kotaAsal, kotaTujuan, berat, ekspedisi[0])
                dataOngkirJne   = cekTarif(kotaAsal, kotaTujuan, berat, ekspedisi[1])
                dataOngkirPos   = cekTarif(kotaAsal, kotaTujuan, berat, ekspedisi[2])
                
                self.context['jumlahBarang']    = request.GET['jumlahBarang']
                self.context['method']          = request.GET['method']
                self.context['slugify']         = request.GET['slugify']
                self.context['id_transaksi']    = id_transaksi
                self.context['alamat']          = alamat
                self.context['kontak']          = kontak
                self.context['ekspedisi']       = ekspedisi
                self.context['tiki']            = templateRajaOngkir(dataOngkirTiki[0]['costs'], dataOngkirTiki[0]['code'])
                self.context['jne']             = templateRajaOngkir(dataOngkirJne[0]['costs'], dataOngkirTiki[0]['code'])
                self.context['pos']             = templateRajaOngkir(dataOngkirPos[0]['costs'], dataOngkirTiki[0]['code'])
                self.context['userAlamat']      = saveAlamat

                return render(self.request, 'address/leftBar2.html', self.context)
            
            if self.action == 'xendit':
                data = makeInvoice(request.GET['id_transaksi'], request.user.email, request.GET['description'], str(request.GET['amount']))
                print(request.GET)
                return JsonResponse(data)

            if self.action == 'subscribe':
                email = request.GET['email']
                subscribe = Subscribe.objects.all()
                emailSubscribe = []
                for eml in subscribe:
                    emailSubscribe.append(eml.email)

                if email in emailSubscribe:
                    return JsonResponse({'success': 'false'})
                else:
                    Subscribe.objects.create(email = email)
                    html = render_to_string('email/subscribe.html', {})
                    msg = EmailMessage(
                        'Selamat datang di Three Laptop',
                        html,
                        'jusles363@gmail.com',
                        [email]
                    )
                    msg.content_subtype = 'html'
                    msg.send()
                    return JsonResponse({'success': 'true'})

            if self.action == 'sort':
                if kwargs['typeSort'] == 'barangMurah':
                    sort = 'harga'
                if kwargs['typeSort'] == 'barangMahal':
                    sort = '-harga'
                if kwargs['typeSort'] == 'barangAZ':
                    sort = 'nama'
                if kwargs['typeSort'] == 'barangZA':
                    sort = '-nama'
                
                page = 1
                barang = Barang.objects.all().order_by(sort)
                barangAll = barang
                if 'pagination' in request.GET:
                    if int(request.GET['pagination']) > 1:
                        start   = (int(request.GET['pagination']) - 1) * 9
                        end     = start * 2
                        barangAll = barang[start:end]
                        page = int(request.GET['pagination'])

                self.context['pagination'] = math.ceil(len(barangAll) / 9)
                paginationNumber = [page, page + 1, page + 2]
                self.context['paginationNumber'] = paginationNumber

                barangLane = [[], []]
                for brng in barangAll:
                    if len(barangLane[1]) == 9:
                        break
                    barangLane[1].append(brng)
                        
                self.context['barangLane'] = barangLane
                self.context['url'] = '/ajax/sort/' + kwargs['typeSort']
                return render(self.request, 'listBarang.html', self.context)

        else:
            return redirect('index')
        return HttpResponse("ajax django")

class Test(TemplateView):
    template_name = 'email/goods.html'
