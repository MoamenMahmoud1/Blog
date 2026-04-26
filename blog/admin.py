from django.contrib import admin
from .models import Post , Comment


@admin.register(Post)  # تسجيل نموذج Post في لوحة تحكم Django باستخدام ديكور @admin.register
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish', 'status' , 'id']  
    # تحديد الأعمدة التي ستظهر في صفحة قائمة المنشورات داخل لوحة التحكم

    list_filter = ['status', 'created', 'publish','author']  
    # إضافة فلاتر جانبية لتصفية المنشورات حسب الحالة، تاريخ الإنشاء، تاريخ النشر، أو الكاتب

    search_fields = ['title', 'body']  
    # تمكين البحث داخل قائمة المنشورات باستخدام عنوان المنشور أو محتوى المنشور

    prepopulated_fields = {'slug': ('title',)}  
    # ملء حقل slug تلقائيًا بناءً على عنوان المنشور عند كتابته

    raw_id_fields = ['author']  
    # استبدال قائمة اختيار المؤلف بزر بحث متقدم، وهو مفيد عند وجود عدد كبير من المستخدمين

    date_hierarchy = 'publish'  
    # إضافة شريط تنقل زمني يسمح بفرز المنشورات حسب تاريخ النشر

    ordering = ['status', 'publish']  
    # تحديد الترتيب الافتراضي للمنشورات بحيث يتم الترتيب حسب الحالة أولًا، ثم حسب تاريخ النشر

    show_facets = admin.ShowFacets.ALWAYS
    # إجبار Django Admin على إظهار واجهة التصفية دائمًا، حتى لو لم تكن هناك نتائج تصفية

# Register your models here.





@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'created', 'active']
    list_filter = ['active', 'created', 'updated']
    search_fields = ['name', 'email', 'body']