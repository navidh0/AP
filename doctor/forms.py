from django import forms
from .models import Comment



class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['title', 'description', 'doctor_rating', 'is_anonymous']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter a title for your review'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Share your experience with this doctor...'
            }),
            'doctor_rating': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            })
        }

        labels = {
            'title': 'Review Title',
            'description': 'Your Review',
            'doctor_rating': 'Rating',
            'is_anonymous': 'Post anonymously'
        }
