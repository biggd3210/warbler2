"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.drop_all()
    db.create_all()

class MessageModelTestCase(TestCase):
    """Test Message Model attributes and methods."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            u1 = User.signup("test1", "test1@email.com", "password", None)
            uid1 = 1111
            u1.id = uid1

            db.session.commit()

            u1 = db.session.get(User, uid1)

            self.u1 = u1
            self.uid1 = uid1

            self.client = app.test_client()

    def teatDown(self):
        """super teardown and reset, empty query"""

        with app.app_context():
            res = super().teardown()
            db.session.rollback()
            return res
        
    def test_message_model(self):
        """Does the model appropriately create a new message?"""

        with app.app_context():
            u1 = db.session.get(User, self.uid1)
            u1.id = self.uid1

            message = Message(text="Test Message",
                            user_id=u1.id)
            mid1 = 1111
            message.id = mid1
            db.session.add(message)
            db.session.commit()

            message = db.session.get(Message, mid1)
            u1 = db.session.get(User, self.uid1)

            self.assertEqual(message.user, u1)
            self.assertEqual(message.text, "Test Message")
            self.assertEqual(message.user_id, u1.id)

            self.assertEqual(len(u1.messages), 1)
            self.assertEqual(u1.messages[0].text, "Test Message")

    def test_message_likes(self):
        """test that likes are tracked through db and accessible through relationships"""

        with app.app_context():
            m1 = Message(text="Test warble",
                         user_id=self.uid1)
            m1.id = 1111
            
            m2 = Message(text="A second warble",
                         user_id=self.uid1)
            m2.id = 2222
            
            u1 = db.session.get(User, self.uid1)

            u2 = User.signup("test4", "test4@email.com", 'password', None)
            u2.id = 4444
            db.session.add_all([m1, m2, u1, u2])
            db.session.commit()

            m1 = db.session.get(Message, 1111)
            m2 = db.session.get(Message, 2222)
            u2 = User.query.filter(User.id == 4444).first()
            u2.likes.append(m1)
            db.session.commit()
            likes = Likes.query.filter(Likes.user_id == u2.id).all()
            u2 = User.query.filter(User.id == 4444).first()
            
            self.assertEqual(len(u2.likes), 1)
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].message_id, m1.id)