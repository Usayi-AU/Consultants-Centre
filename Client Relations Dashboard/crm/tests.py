from django.test import TestCase
from django.urls import reverse

from crm.models import ActionItem


class UnlockAccessFlowTests(TestCase):
    def setUp(self):
        ActionItem.objects.create(
            client='Alpha Client',
            action_item='Prepare proposal',
            status='Open',
            owner='Tari',
        )
        ActionItem.objects.create(
            client='Beta Client',
            action_item='Confirm invoice',
            status='Open',
            owner='Shandu',
        )

    def test_dashboard_requires_unlock(self):
        response = self.client.get(reverse('crm:dashboard'))
        self.assertRedirects(response, reverse('crm:unlock_access'))

    def test_general_passkey_allows_access(self):
        response = self.client.post(reverse('crm:unlock_access'), {'passkey': '10'})
        self.assertRedirects(response, reverse('crm:dashboard'))

        response = self.client.get(reverse('crm:client_action_items'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alpha Client')
        self.assertContains(response, 'Beta Client')

    def test_owner_passkey_filters_action_items_and_allows_edit(self):
        response = self.client.post(reverse('crm:unlock_access'), {'passkey': 'Tari'})
        self.assertRedirects(response, reverse('crm:dashboard'))

        response = self.client.get(reverse('crm:client_action_items'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alpha Client')
        self.assertNotContains(response, 'Beta Client')

        item = ActionItem.objects.get(owner='Tari')
        response = self.client.get(reverse('crm:edit_action_item', args=[item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_admin_passkey_allows_full_access(self):
        response = self.client.post(reverse('crm:unlock_access'), {'passkey': 'tari.crm@'})
        self.assertRedirects(response, reverse('crm:dashboard'))

        response = self.client.get(reverse('crm:client_action_items'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alpha Client')
        self.assertContains(response, 'Beta Client')

    def test_invalid_passkey_shows_error(self):
        response = self.client.post(reverse('crm:unlock_access'), {'passkey': 'bad-key'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid passkey')

    def test_owner_can_create_new_action_item(self):
        self.client.post(reverse('crm:unlock_access'), {'passkey': 'Tari'})

        response = self.client.post(reverse('crm:create_action_item'), {
            'client': 'New Client',
            'action_item': 'Prepare onboarding document',
            'status': 'Open',
            'owner': 'Tari',
            'date_received': '',
            'target_date': '',
            'completion_date': '',
            'update_prev_week': '',
            'update_this_week': '',
        })

        self.assertRedirects(response, reverse('crm:client_detail', args=['New Client']))
        self.assertTrue(ActionItem.objects.filter(client='New Client', owner='Tari').exists())

    def test_admin_can_create_action_item_and_view_activity(self):
        self.client.post(reverse('crm:unlock_access'), {'passkey': 'tari.crm@'})

        response = self.client.post(reverse('crm:create_action_item'), {
            'client': 'Admin Client',
            'action_item': 'Approve budget',
            'status': 'In Progress',
            'owner': 'Shandu',
            'date_received': '',
            'target_date': '',
            'completion_date': '',
            'update_prev_week': '',
            'update_this_week': '',
        })

        self.assertRedirects(response, reverse('crm:client_detail', args=['Admin Client']))

        response = self.client.get(reverse('crm:admin_activity'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Client')
        self.assertContains(response, 'Created by Admin')

    def test_owner_cannot_access_admin_activity(self):
        self.client.post(reverse('crm:unlock_access'), {'passkey': 'Tari'})

        response = self.client.get(reverse('crm:admin_activity'))
        self.assertEqual(response.status_code, 403)

    def test_exit_dashboard_clears_session_and_requires_unlock_again(self):
        self.client.post(reverse('crm:unlock_access'), {'passkey': 'Tari'})

        response = self.client.post(reverse('crm:exit_dashboard'))
        self.assertRedirects(response, reverse('crm:unlock_access'))

        response = self.client.get(reverse('crm:dashboard'))
        self.assertRedirects(response, reverse('crm:unlock_access'))

    def test_admin_can_delete_specific_history_record(self):
        self.client.post(reverse('crm:unlock_access'), {'passkey': 'tari.crm@'})

        self.client.post(reverse('crm:create_action_item'), {
            'client': 'Delete Trail Client',
            'action_item': 'Remove this entry later',
            'status': 'Open',
            'owner': 'Tari',
            'date_received': '',
            'target_date': '',
            'completion_date': '',
            'update_prev_week': '',
            'update_this_week': '',
        })

        entry = ActionItem.objects.get(client='Delete Trail Client').history.first()

        response = self.client.post(reverse('crm:delete_history', args=[entry.pk]))
        self.assertRedirects(response, reverse('crm:admin_activity'))
        self.assertFalse(entry.__class__.objects.filter(pk=entry.pk).exists())
