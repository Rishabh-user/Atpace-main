from django.test import TestCase, Client
from apps.leaderboard.urls import *
from django.urls import reverse
from apps.users.models import User


class TestUrls(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('shru', 'shrutika@gmail.com', 'Pass@1234')

    def test_create_goal(self):
        client = Client()
        client.login(username='shru', password='Pass@1234')
        # testing create post
        response = client.post(reverse('leaderboard:goal'), {'heading': 'test', 'description': 'test', 'category': 'Learn',
                                                             'frequency': 'Daily', 'priority': 'Normal', 'duration_number': '20', 'duration_time': 'Mins'})
        # print("response", response)
        self.assertEqual(response.status_code, 302)

        # testing view goal
        goal_list = client.get(reverse('leaderboard:goal'))
        # print("response goal", goal_list.context)
        self.assertEqual(goal_list.status_code, 200)
        self.assertTrue('data' in goal_list.context)
        self.assertTrue('category_list' in goal_list.context)

        # testing delete goal
        delete_goal = client.post(reverse('leaderboard:delete_goal'), kwargs={
                                  'id': '601fb8fa-d88b-40e3-99b3-f8735d2defb6'})
        self.assertTrue(delete_goal)

        # testing goal progress
        goal_progress = client.get('/leaderboard/user-goal-progress/601fb8fa-d88b-40e3-99b3-f8735d2defb6/')

        self.assertTrue(goal_progress)
        self.assertEqual(goal_progress.status_code, 200)

        # testing user goal log
        goal_log = client.post(reverse('leaderboard:user_goal_log'), {
                               'id': '601fb8fa-d88b-40e3-99b3-f8735d2defb6', 'status': 'Completed'})
        self.assertTrue(goal_log)

        print(goal_log)

    # def test_goal_url(self):
    #     client = Client()
    #     client.login(username='shru', password='Pass@1234')
    #     # self.client.login(email='prashantk794@gmail.com', password='Pass@1234')
    #     response = client.get(reverse('leaderboard:goal'))
    #     print("response", response)
    #     self.assertTemplateUsed(response, 'goals.html')
    #     self.assertEqual(response.status_code, 200)

    # def test_view_goal_url(self):
    #     self.client.login(username='shru', password='Pass@1234')
    #     response = self.client.get(reverse('leaderboard:view_goal'))
    #     self.assertEqual(response.status_code, 200)

    # def test_delete_goal_url(self):
    #     response = self.client.get('/leaderboard/delete-goal/')
    #     self.assertEqual(response.status_code, 302)

    # def test_user_goal_log_url(self):
    #     response = self.client.get('/leaderboard/user-goal-log/')
    #     self.assertEqual(response.status_code, 302)
