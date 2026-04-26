from django.views.generic import ListView
from django.shortcuts import render , get_object_or_404 , redirect
from .models import Post
from django.http import Http404 
from django.core.paginator import Paginator , EmptyPage , PageNotAnInteger
from .forms import EmailPostForm 
from django.core.mail import send_mail
from taggit.models import Tag


from django.db.models import Count
# Create your views here.


 
def post_list(request , tag_slug=None):
     post_list = Post.published.all()
     
     
     #===============Tag===============#
     tag = None
     
     
     
     
     if tag_slug:
          tag = get_object_or_404(Tag , slug=tag_slug)
          post_list = post_list.filter(tags__in=[tag])
          #=================================#
     # Pagination with 3 posts per page
     paginator = Paginator(post_list, 3)
     page_number = request.GET.get('page')
     try:
          posts = paginator.page(page_number)
     except PageNotAnInteger:
          # If page_number is not an integer get the first page
          posts = paginator.page(1)
     except EmptyPage:
          # If page_number is out of range get last page of results
          posts = paginator.page(paginator.num_pages)
     return render(
     request,
     'post/list.html',
     {'posts': posts , 'tag':tag}
)
"""

class PostListView(ListView):
     queryset = Post.published.all()
     context_object_name = 'posts'
     paginate_by = 3
     template_name = 'post/list.html'
     
          
"""

def post_detail(request,year,month,day,post):
     post = get_object_or_404(Post,status=Post.Status.PUBLISHED,slug=post,publish__year=year,publish__month=month,publish__day=day)
     
     # List of active comments for this post
     comments = post.comments.filter(active=True)
     form = CommentForm()
     post_tags_ids = post.tags.values_list('id',flat=True)
     similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
     similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
     
     return render(request ,'post/detail.html' , {'post':post , 'comments':comments , 'form':form , 'similar_posts':similar_posts})





def post_share(request , post_id):
     #retreive post by id
     post = get_object_or_404(Post , id=post_id , status=Post.Status.PUBLISHED)
     sent = False
     
     if request.method == 'POST':
          #form was submmited
          form = EmailPostForm(request.POST)
          if form.is_valid():
               #form fields passed validation
               cd = form.cleaned_data
               post_url = request.build_absolute_uri(post.get_absolute_url())
               subject = (f"{cd['name']} ({cd['email']}) "f"recommends you read {post.title}")
               message = (f"Read {post.title} at {post_url}\n\n"f"{cd['name']}\'s comments: {cd['comments']}")
               send_mail(subject=subject,message=message,from_email=None,recipient_list=[cd['to']])
               sent = True
               
               # send Email
     else:
          form = EmailPostForm()
     return render(request , 'post/share.html' , {'post':post , 'form':form , 'sent':sent})          
     
     

#===================================================================


from django.views.decorators.http import require_POST
from django.views.generic import ListView
from .forms import CommentForm , EmailPostForm , SearchForm
from django.contrib.postgres.search import (SearchVector,SearchQuery,SearchRank)



@require_POST


def post_comment(request , post_id):
     print("post_id:",post_id)
     post = get_object_or_404(Post , id=post_id , status=Post.Status.PUBLISHED)
     comment = None
     
     # استلام البيانات المرسلة في النموذج والتحقق منها
     form = CommentForm(data=request.POST)
     
     
     if form.is_valid():
          # إنشاء كائن تعليق جديد بدون حفظه مباشرةً
          comment = form.save(commit=False)
          # ربط التعليق بالمنشور الحالي
          comment.post = post
          # حفظ التعليق في قاعدة البيانات
          comment.save()
          
          
     return render(request , "post/comment.html" , {"form":form,"post":post , "comment":comment})


def post_search(request):
     form = SearchForm()
     query = None
     results = []
     if 'query' in request.GET:
          form = SearchForm(request.GET)
          if form.is_valid():
               query = form.cleaned_data['query']
               search_vector = SearchVector('title', 'body', config='spanish')
               search_query = SearchQuery(query, config='spanish')
               results = (
               Post.published.annotate(
               search=search_vector,rank=SearchRank(search_vector, search_query)
               ).filter(search=search_query).order_by('-rank'))
     return render(
     request,
     'post/search.html',
     {
     'form': form,
     'query': query,
     'results': results
     }
     )