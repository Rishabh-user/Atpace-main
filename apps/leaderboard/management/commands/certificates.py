from apps.content.models import CertificateTemplate, UserCertificate, UserChannel
from django.db import transaction
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "check data from csv"

    @transaction.atomic
    def handle(self, *args, **options):
        all_users = UserChannel.objects.all()

        for user in all_users:
            try:
                user_cert_obj = UserCertificate.objects.get(user=user.user, journey=user.Channel)
                cert_obj = CertificateTemplate.objects.get(journey=user.Channel)
                user_cert_obj.certificate_template = cert_obj
                user_cert_obj.save()
                try:
                    self.stdout.write(self.style.SUCCESS(f"Certificate updated for {user.user.email} for {user.Channel.title}"))
                    self.stdout.write(self.style.SUCCESS(f"URL={user_cert_obj.file.url}"))
                    print(f"URL={user_cert_obj.file.url}")
                except Exception as ee:
                    self.stdout.write(self.style.ERROR(f"No url reason = {str(ee)}"))
            except Exception as e:
                continue
                # print(f"Error for {user.user.email} because {str(e)}")
                # self.stdout.write(self.style.ERROR(f"Error for {user.user.email} because {str(e)} for {user.Channel.title}"))   
                
                

