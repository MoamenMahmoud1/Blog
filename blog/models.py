from django.db import models
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from taggit.managers import TaggableManager
#from django.db.models.functions import Now



# ========{Post}========
#=================================================================================================================================

class PublishedManager(models.Manager):
    def get_queryset(self):
        
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)

#===============================================
class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'
#===============================================

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250 , unique_for_date='publish')
    body = models.TextField()
    publish = models.DateTimeField(default=timezone.now)
    #publish = models.DateTimeField(db_default=Now())
    created =  models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2, choices=Status, default=Status.DRAFT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='blog_posts') # many to one
    objects = models.Manager()  
    published = PublishedManager()  

#===============================================

    tags = TaggableManager()

#===============================================
    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]
#===============================================
    def __str__(self):
        return self.title
#===============================================
    
    def get_absolute_url(self):
        """
        Return the absolute URL of this post.
        
        Example: /blog/2022/01/01/my-first-post/
        
        This method is used in the template to generate a link to the post.
        """
        return reverse(viewname='blog:post_detail' , args=[self.publish.year , self.publish.month , self.publish.day , self.slug])
    
    
    
    
    
    
#================={Comment} (Row / Colmun)

# MODULES





#===========================================

class Comment(models.Model):
    post = models.ForeignKey(Post  ,  on_delete=models.CASCADE  ,  related_name='comments')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    class Meta:
        ordering = ['created']
        indexes = [
        models.Index(fields=['created']),
        ]
    def __str__(self):
        return f'Comment by {self.name} on {self.post}'
