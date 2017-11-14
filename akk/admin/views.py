import flask_admin as admin
from flask_admin.contrib import sqla

# Create admin
from akk.common.models import db
from akk.songs.models import Song, Artist, Dance, Label, Rating
from akk.users.models import User

admin = admin.Admin(name='Example: SQLAlchemy', template_mode='bootstrap3')

# Add views
admin.add_view(sqla.ModelView(User, db.session))
admin.add_view(sqla.ModelView(Song, db.session))
admin.add_view(sqla.ModelView(Artist, db.session))
admin.add_view(sqla.ModelView(Dance, db.session))
admin.add_view(sqla.ModelView(Label, db.session))
admin.add_view(sqla.ModelView(Rating, db.session))