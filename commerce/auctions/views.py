from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User,Category,Listening,Comment,Bid

def listing(request,id):
    listingData = Listening.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request,"auctions/listing.html",{
        "listing": listingData,
        "isListingInWatchlist" : isListingInWatchlist,
        "allComments": allComments,
        "isOwner" :isOwner,
    })

def closeAuction(request,id):
    listingData = Listening.objects.get(pk=id)
    listingData.isActive = False
    listingData.save()
    isOwner = request.user.username == listingData.owner.username
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    return render(request,"auctions/listing.html",{
        "listing": listingData,
        "isListingInWatchlist" : isListingInWatchlist,
        "allComments": allComments,
        "isOwner" : isOwner,
        "updated" :True,
        "message" : "Congratulations! Your auction is closed "
    })

def addBid(request,id):
    newBid = request.POST['newBid']
    listingData = Listening.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    if int(newBid) > listingData.price.bid:
        updateBid = Bid(user = request.user, bid = int(newBid))
        updateBid.save()
        listingData.price = updateBid
        listingData.save()
        return render(request, "auctions/listing.html",{
            "listing" :listingData,
            "message" :"Bid was updated succesfully",
            "update" :True,
            "isOwner" : isOwner,

        })
    else:
        return render(request, "auctions/listing.html",{
            "listing" :listingData,
            "message" :"Bid was updated failed",
            "update" :False 
        })

def addComment(request, id):
    currentUser = request.user
    listingData = Listening.objects.get(pk=id)
    newCommentMessage = request.POST['newComment'] 

    # Yorum oluşturma
    newComment = Comment(
        author=currentUser,
        listing=listingData,
        message=newCommentMessage 
    )

    # Yorum kaydetme
    newComment.save()

    return HttpResponseRedirect(reverse("listing", args=(id,)))

def displayWatchlist(request):
    currentUser = request.user
    listings = currentUser.listingWatchlist.all() 
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def addWatchlist(request, id):
    listingData = Listening.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id,)))

def removeWatchlist(request, id):
    listingData = Listening.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect(reverse("listing", args=(id,)))


def index(request):
    activeListening = Listening.objects.filter(isActive=True)
    allCategories  = Category.objects.all()
    return render(request, "auctions/index.html",{
       "listenings": activeListening,
       "categories":allCategories,
    })

def displayCategory(request):
    if request.method == "POST":
        categoryFromForm =request.POST['category']
        category =Category.objects.get(categoryName=categoryFromForm)
        # Bunun sebebi zaten isActive olanları almak istiyordum ben ondan dolayı
        activeListening = Listening.objects.filter(isActive=True, category = category)
        allCategories  = Category.objects.all()
        return render(request, "auctions/index.html",{
        "listenings": activeListening,
        "categories":allCategories,
        })



def createListening(request):
    if request.method == "GET":
        allCategories  = Category.objects.all()
        return render(request, "auctions/create.html" ,{
            "categories" :allCategories
        })
    else:
        #Get data from the from
        title = request.POST["title"]
        description = request.POST["description"]
        imageurl = request.POST["imageurl"]
        price = request.POST["price"]
        category = request.POST["category"]
        #belgeyi hangi kullancı ekledi
        currentUser = request.user
        #tüm verileri almam lazım yoksa hata alıyorum 
        categoryData = Category.objects.get(categoryName=category)
        #yeni bir bit object oluşturduk
        bid = Bid(bid = float(price), user = currentUser)
        bid.save()
        #Yeni bir liste oluşturma
        newListening = Listening(
            title = title,
            description = description,
            imageUrl = imageurl,
            price = bid,
            category = categoryData,
            owner = currentUser
        )
        #database e verileri kaydedicek kod
        newListening.save()
        #direk başka bir sayfaya gönderme
        return HttpResponseRedirect(reverse(index))

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
