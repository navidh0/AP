from django import forms

class TailwindFormMixin:
    """
    Mixin that applies Tailwind CSS classes to form fields.
    """

    input_classes = (
        "w-full input-field border border-neutral-300 rounded-xl py-3 px-4 "
        "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent "
        "transition duration-200 ease-out"
    )

    file_classes = "hidden"

    def apply_tailwind_classes(self):
        """Apply Tailwind classes to fields dynamically."""
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                field.widget.attrs.update({
                    "class": self.input_classes,
                    "autocomplete": "off",
                })
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({
                    "class": self.file_classes
                })
            else:
                field.widget.attrs.update({
                    "class": self.input_classes,
                })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()
