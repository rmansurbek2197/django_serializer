from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Author, Category, Book
from django.utils import timezone


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ['slug']

        def validate_price(self, value):
            if value < 0:
                raise serializers.ValidationError("Narx 0 dan kichik bo'lishi mumkin emas")
            if value < 10000:
                raise serializers.ValidationError("Narx 10000 dan katta bo'lmasligi kerak")
            return value

        
        def validate(self, data):
            published_date = data.get('published_date')
            stock_count = data.get('stock_count')
            is_bestseller = data.get('is_bestseller')


            if published_date and published_date > timezone.now().date()
                raise serializers.ValidationError("Nashr sanasi kelajakdagi sana bo'lishi mumkin emas")
            if stock_count == 0 and is_bestseller:
                raise serializers.ValidationError("Zaxirada bo'lmagan kitob bestseller bola olmaydi")
            return data

        def update(self, instance, validated_data):
            new_price = validated_data.get('price')
            if new_price is not None:
                old_price = instance.price
                if old_price != 0:
                    diff_percent = abs(new_price - old_price) / old_price * 100
                    if diff_percent > 50:
                        raise serializers.ValidationError(
                            f"Narx o'zgarishi 50% dan oshmasligi kerak"
                        )
            return super().update(instance, validated_data)

        def to_representation(self, instance):
            rep = super().to_representation(instance)
            rep['author_name'] = instance.author.full_name
            del rep['author']
            rep['category_names'] = [cat.name for cat in instance.categories.all()]
            del rep['categories']
            return rep

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'full_name', 'birth_date', 'email', 'is_active']

class BookCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=250)
    author = NestedAuthorSerializer()
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    published_date = serializers.DateField(required=False, allow_null=True)
    is_bestseller = serializers.BooleanField(default=False)
    stock_count = serializers.IntegerField(default=0)
    slug = serializers.SlugField(required=False, allow_blank=True)

    def create(self, validated_data):
        author_data = validated_data.pop('author')
        categories = validated_data.pop('categories')

        email = author_data.get('email')
        author, _ = Author.objects.get_or_create(
            email=email,
            defaults=author_data
        )
        if not _:
            for attr, value in author_data.items():
                setattr(author, attr, value)
            author.save()

        book = Book.objects.create(author=author, **validated_data)
        book.categories.set(categories)
        return book
    
    def update(self, instance, validated_data):
        raise NotImplementedError("Ushbu serializer faqat create uchun mo'ljallangan")
    

class BookDynamicSerializer(BookSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class BookWithUniqueTitleAuthorSerializer(serializers.ModelSerializer):
    



