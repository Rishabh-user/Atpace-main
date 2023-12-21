import csv
from django.db import transaction
from django.core.management.base import BaseCommand

from apps.users.models import User
from apps.leaderboard.models import PointsTable, StreakPoints, BadgeDetails

class Command(BaseCommand):
    help = "Populate data from csv into points, Streaks and Badge table"

    StreakPoints.objects.all().delete()
    BadgeDetails.objects.all().delete()
    @transaction.atomic
    def handle(self, *args, **options):
#         try:
#             with open("static/csv/PointsTable.csv") as csv_file:
#                 reader = csv.DictReader(csv_file)
#                 for row in reader:
#                     try:
#                         user= User.objects.get(username=row['created_by'])
#                     except User.DoesNotExist:
#                         return self.stdout.write("user does not exist")
#                     points = PointsTable(name=row['name'], label=row['label'], points=row['points'],
#                                          comment=row['comment'], created_by=user)
#                     points.save()
#                 print(self.style.SUCCESS("Points are created"))
#         except Exception as e:
#             print(e)

        try:
            with open("static/csv/StreaksDataset.csv") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    try:
                        user= User.objects.get(username=row['created_by'])
                    except User.DoesNotExist:
                        return self.stdout.write("user does not exist")
                    points = StreakPoints(name=row['name'], duration_in_days=row['duration_in_days'], points=row['points'],
                                         comment=row['comment'], created_by=user)
                    points.save()
                print(self.style.SUCCESS("Streaks are created"))
        except Exception as e:
            print(e)

        
        try:
            with open("static/csv/BadgesDataset.csv") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    try:
                        user= User.objects.get(username=row['created_by'])
                    except User.DoesNotExist:
                        return self.stdout.write("user does not exist")
                    try:
                        print(row['label'])
                        points= PointsTable.objects.get(label=row['label'])
                    except PointsTable.DoesNotExist:
                        return self.stdout.write("points does not exist")
                    badges = BadgeDetails(name=row['name'], description=row['description'], image=row['image'],
                                        label=points, points_required=row['points_required'],
                                        badge_for=row['badge_for'], is_active=row['is_active'], created_by=user)
                    badges.save()
                print(self.style.SUCCESS("badges are created"))
        except Exception as e:
            print(e)
            return(e)
        self.stdout.write(self.style.SUCCESS("All Done!"))



# class Command(BaseCommand):
    
#     help = "Populate data from StreaksDataset.csv into StreaksPoint table"
    
#     StreakPoints.objects.all().delete()
#     @transaction.atomic
#     def handle(self, *args, **options):
#         try:
#             with open("static/csv/StreaksDataset.csv") as csv_file:
#                 reader = csv.DictReader(csv_file)
#                 for row in reader:
#                     try:
#                         user= User.objects.get(username=row['created_by'])
#                     except User.DoesNotExist:
#                         return self.stdout.write("user does not exist")
#                     points = StreakPoints(name=row['name'], duration_in_days=row['duration_in_days'], points=row['points'],
#                                          comment=row['comment'], created_by=user)
#                     points.save()
#                     # print(points)
#         except Exception as e:
#             print(e)
#             return(e)
#         self.stdout.write("All Done!")