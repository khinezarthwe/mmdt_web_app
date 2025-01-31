from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def confirm_email(self, request, email_address):
        """
        Override email confirmation to set user as inactive
        """
        email_address.verified = True
        email_address.save()
        email_address.user.is_active = False  # Set user to inactive
        email_address.user.save()
        return email_address

