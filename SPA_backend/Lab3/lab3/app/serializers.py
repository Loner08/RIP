from rest_framework import serializers

from .models import *


class ConsumersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumer
        fields = ("id", "name", "status", "power", "category", "image")


class ConsumerSerializer(ConsumersSerializer):
    class Meta(ConsumersSerializer.Meta):
        fields = "__all__"


class ReservesSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    moderator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Reserve
        fields = "__all__"


class ReserveSerializer(ReservesSerializer):
    consumers = serializers.SerializerMethodField()
            
    def get_consumers(self, reserve):
        items = reserve.consumerreserve_set.all()
        return [ConsumerItemSerializer(item.consumer, context={"percentage": item.percentage}).data for item in items]


class ConsumerItemSerializer(ConsumerSerializer):
    percentage = serializers.SerializerMethodField()

    def get_percentage(self, _):
        return self.context.get("percentage")

    class Meta:
        model = Consumer
        fields = ("id", "name", "status", "power",  "category", "image", "percentage")


class ConsumerReserveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsumerReserve
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', "is_superuser")


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class UserUpdateProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        instance = super().update(instance, validated_data)

        if password and password.strip() and not self.instance.check_password(password):
            instance.set_password(password)
            instance.save()

        return instance