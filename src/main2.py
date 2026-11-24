from typing import Annotated

# class MyClass:
#     def __getitem__(self, key):
#         print(f"Accessing key: {key}")
#         return f"Value for {key}"

#     def __class_getitem__(cls, key):
#         print(f"Accessing class key: {key}")
#         return f"Class value for {key}"

# c = MyClass()
# c[1:10:2]





# class _SpecialForm:
#     def __class_getitem__(cls, params):
#         print(f"__class_getitem__ 被调用，cls = {cls}, type(cls) = {type(cls)}")
#         return "result"
#
# Annotated = _SpecialForm()
# print(Annotated[int, "abc"])
