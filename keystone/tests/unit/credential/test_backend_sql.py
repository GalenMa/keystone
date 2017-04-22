# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from six.moves import range

from keystone.credential.providers import fernet as credential_provider
from keystone.tests import unit
from keystone.tests.unit import default_fixtures
from keystone.tests.unit import ksfixtures
from keystone.tests.unit.ksfixtures import database


class SqlTests(unit.SQLDriverOverrides, unit.TestCase):

    def setUp(self):
        super(SqlTests, self).setUp()
        self.useFixture(database.Database())
        self.load_backends()
        # populate the engine with tables & fixtures
        self.load_fixtures(default_fixtures)
        # defaulted by the data load
        self.user_foo['enabled'] = True

    def config_files(self):
        config_files = super(SqlTests, self).config_files()
        config_files.append(unit.dirs.tests_conf('backend_sql.conf'))
        return config_files


class SqlCredential(SqlTests):

    def _create_credential_with_user_id(self, user_id=None):
        if not user_id:
            user_id = uuid.uuid4().hex
        credential = unit.new_credential_ref(user_id=user_id,
                                             extra=uuid.uuid4().hex,
                                             type=uuid.uuid4().hex)
        self.credential_api.create_credential(credential['id'], credential)
        return credential

    def _validate_credential_list(self, retrieved_credentials,
                                  expected_credentials):
        self.assertEqual(len(expected_credentials), len(retrieved_credentials))
        retrieved_ids = [c['id'] for c in retrieved_credentials]
        for cred in expected_credentials:
            self.assertIn(cred['id'], retrieved_ids)

    def setUp(self):
        super(SqlCredential, self).setUp()
        self.useFixture(
            ksfixtures.KeyRepository(
                self.config_fixture,
                'credential',
                credential_provider.MAX_ACTIVE_KEYS
            )
        )
        self.credentials = []
        self.user_credentials = []
        # setup 3 credentials with random user ids
        for _ in range(3):
            cred = self._create_credential_with_user_id()
            self.user_credentials.append(cred)
            self.credentials.append(cred)
        # setup 3 credentials with specific user ids
        for _ in range(3):
            cred = self._create_credential_with_user_id(self.user_foo['id'])
            self.user_credentials.append(cred)
            self.credentials.append(cred)

    def test_backend_credential_sql_hints_none(self):
        credentials = self.credential_api.list_credentials(hints=None)
        self._validate_credential_list(credentials, self.user_credentials)

    def test_backend_credential_sql_no_hints(self):
        credentials = self.credential_api.list_credentials()
        self._validate_credential_list(credentials, self.user_credentials)
