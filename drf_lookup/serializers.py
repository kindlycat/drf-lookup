from rest_framework import serializers


class LookupQuerysetSerializer(serializers.Serializer):
    """Serializer for queryset lookups.

    This serializer is used to represent a queryset lookup with read-only
    fields for the primary key and string representation of the object.

    Attributes:
        id (ReadOnlyField): The primary key of the object.
        name (ReadOnlyField): The string representation of the object.
    """

    id = serializers.ReadOnlyField(source='pk')
    name = serializers.ReadOnlyField(source='__str__')


class LookupChoiceSerializer(serializers.Serializer):
    """Serializer for choice lookups.

    This serializer is used to represent a choice lookup with methods to get
    the id and name from a tuple.

    Attributes:
        id (SerializerMethodField): The value in the db of the choice.
        name (SerializerMethodField): The name of the choice.
    """

    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    @staticmethod
    def get_id(obj) -> int | str:
        """Get the value in the db from the choice tuple.

        Args:
            obj (tuple): The choice tuple.

        Returns:
            int | str: The value in the db of the choice.
        """
        return obj[0]

    @staticmethod
    def get_name(obj) -> str:
        """Get the name from the choice tuple.

        Args:
            obj (tuple): The choice tuple.

        Returns:
            str: The name of the choice.
        """
        return obj[1]
