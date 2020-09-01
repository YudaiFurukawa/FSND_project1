#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#


import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_wtf.csrf import CSRFProtect
from forms import *
from flask_migrate import Migrate, MigrateCommand
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
# csrf = CSRFProtect(app)
# csrf.init_app(app)
moment = Moment(app)
app.config.from_object('config')
# app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Romans08@localhost:5432/project1'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String()))
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy=True, cascade='all, delete')

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True, cascade='all, delete')

    def __repr__(self):
      return f'<Artist {self.id} {self.name}>'

    #TODO : implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
  __tablename__ = 'Show'
  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)



db.create_all()


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
    format = "EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
    format = "EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
#  Controllers.
# ----------------------------------------------------------------------------#

# to render the default home page:
@app.route('/')
def index():
  return render_template('pages/home.html')


#  ----------------------------------------------------------------
#                         Venues Controllers
#  ----------------------------------------------------------------

#  ----------------------------------------------------------------
# Display all venues:
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  # get the results from Venue table based on the city and state only:
  results = db.session.query(Venue).with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  data = []

  # this outer loop will pass to get all the venues related to a specific city
  for item in results:
    city = Venue.query.filter_by(city=item.city).all()

    venue_details = []
    # this inner loop will pass on every venue to get detailed information about venue:(id, name, num_upcoming_shows)
    for venue in city:
      venue_details.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(
          db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all())
      })

    data.append({
      "city": item.city,
      "state": item.state,
      "venues": venue_details
    })

  return render_template('pages/venues.html', areas=data)


#  ----------------------------------------------------------------
# Search in the venues (case-insensitive):
#  ----------------------------------------------------------------
@app.route('/venues/search', methods=['POST'])
def search_venues():
  # get the term the user types:
  search_term = request.form.get('search_term', '')

  # get all the venues names that match the search term
  venues_results = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()

  data = []
  # this loop will pass on every venue to get the required information:(id, name, num_upcoming_shows)
  for venue in venues_results:
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(
        db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all())
    })

  # count is the number of all venues that match the search term:
  count = len(venues_results)

  # respone contains the number of the matching results, and the required data for the venues
  response = {
    "count": count,
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


#  ----------------------------------------------------------------
# Display the information about a spicific venue:
#  ----------------------------------------------------------------
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # get the venue object depending on venue_id
  venue = db.session.query(Venue).get(venue_id)

  # to deal with any error if we cannot obtain the required venue object
  if not venue:
    return render_template('errors/404.html')

  # get all shows related to this specific venue, by joining Show and Artist tables
  venue_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).all()

  current_time = datetime.now()
  past_shows = []
  upcoming_shows = []

  # this loop will pass on every venue_shows, and determine whether this show is past or upcoming
  # and get the required information of the shows
  for show in venue_shows:
    if show.start_time < current_time:
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
      })
    else:
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
      })

  # obtain all the information about the venue to be displayed in the show_venue.html page
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)


#  ----------------------------------------------------------------
#  Create a new Venue:
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    # get the information in the form that the user filled out
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    seeking = request.form['seeking_talent']
    seeking_description = request.form['seeking_description']

    # this condition is to store the correct boolean value (true - false),
    # because the form in the html page displays two choices: "YES" or "NO"
    if seeking == "YES":
      seeking_talent = True
    else:
      seeking_talent = False

    # create a new venue object and add it to the postgres database (fyyurdb)
    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres,
                  facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent,
                  seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Update Venues:
#  ----------------------------------------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # display the form containing the information stored in the database,
  # so that the user can view and change the old data
  form = VenueForm()
  venue = db.session.query(Venue).get(venue_id)

  if not venue:
    return render_template('errors/404.html')

  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.address.data = venue.address
  form.phone.data = venue.phone
  form.genres.data = venue.genres
  form.facebook_link.data = venue.facebook_link
  form.image_link.data = venue.image_link
  form.website.data = venue.website
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # extracting the new values ​​from the modified form to be replaced with the old values and ​​stored in the database
  venue_obj = db.session.query(Venue).get(venue_id)
  try:
    venue_obj.name = request.form['name']
    venue_obj.city = request.form['city']
    venue_obj.state = request.form['state']
    venue_obj.address = request.form['address']
    venue_obj.phone = request.form['phone']
    venue_obj.genres = request.form.getlist('genres')
    venue_obj.facebook_link = request.form['facebook_link']
    venue_obj.image_link = request.form['image_link']
    venue_obj.website = request.form['website']
    seeking = request.form['seeking_talent']
    venue_obj.seeking_talent = True if seeking == "YES" else False
    venue_obj.seeking_description = request.form['seeking_description']
    db.session.commit()
    flash('The venue has been updated successfully.')

  except ValueError as e:
    flash('It was not possible to update this Venue !')

  return redirect(url_for('show_venue', venue_id=venue_id))


#  ----------------------------------------------------------------
# Delete spicific venue from the database depending on venue_id:
# if you delete a venue, all of its shows will be deleted
#  ----------------------------------------------------------------
@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.filter_by(id=venue_id).first_or_404()
    db.session.delete(venue)
    db.session.commit()
    flash('The venue has been removed together with all of its shows.')
    return render_template('pages/home.html')

  except ValueError as e:
    flash('It was not possible to delete this Venue')

  return None


#  ----------------------------------------------------------------
#                        Artists Controllers
#  ----------------------------------------------------------------


#  ----------------------------------------------------------------
# Display all artists:
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # get all artists and display it in artists.html
  data = db.session.query(Artist).all()

  return render_template('pages/artists.html', artists=data)


#  ----------------------------------------------------------------
# Search in the artists (case-insensitive)
#  ----------------------------------------------------------------
@app.route('/artists/search', methods=['POST'])
def search_artists():
  # get the term the user types:
  search_term = request.form.get('search_term', '')
  # get all the atrists names that match the search term
  artists_results = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()

  data = []
  # this loop will pass on every artist to get the required information:(id, name, num_upcoming_shows)
  for artist in artists_results:
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(
        db.session.query(Show).filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all())
    })

  # count is the number of all artists that match the search term:
  count = len(artists_results)

  # respone contains the number of the matching results, and the required data for the artists
  response = {
    "count": count,
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


#  ----------------------------------------------------------------
# display the information about a spicific artist:
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # get the artist object depending on artist_id
  artist = db.session.query(Artist).get(artist_id)

  # to deal with any error if we cannot obtain the required artist object
  if not artist:
    return render_template('errors/404.html')

  # get all shows related to this specific artist, by joining Show and Venue tables
  artist_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).all()

  current_time = datetime.now()
  past_shows = []
  upcoming_shows = []

  # this loop will pass on every artist_shows, and determine whether this show is past or upcoming
  # and get the required information of the shows
  for show in artist_shows:
    if show.start_time < current_time:
      past_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
      })
    else:
      upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
      })

  # obtain all the information about the artist to be displayed in the show_artist.html page
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)


#  ----------------------------------------------------------------
#  Create a new Artist:
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form

  error = False
  try:
    # get the information in the form that the user filled out
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres'),
    facebook_link = request.form['facebook_link']
    image_link = request.form['image_link']
    website = request.form['website']
    seeking = request.form['seeking_venue']
    seeking_description = request.form['seeking_description']

    # this condition is to store the correct boolean value (true - false),
    # because the form in the html page displays two choices: "YES" or "NO"
    if seeking == "YES":
      seeking_venue = True
    else:
      seeking_venue = False

    # create a new artist object and add it to the postgres database (fyyurdb)
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link,
                    image_link=image_link, website=website, seeking_venue=seeking_venue,
                    seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()

  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.' + seeking_venue)

  return render_template('pages/home.html')


#  ----------------------------------------------------------------
#  Update artists:
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = db.session.query(Artist).get(artist_id)

  if not artist:
    return render_template('errors/404.html')

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.facebook_link.data = artist.facebook_link
  form.image_link.data = artist.image_link
  form.website.data = artist.website
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist_obj = db.session.query(Artist).get(artist_id)
  try:
    artist_obj.name = request.form['name']
    artist_obj.city = request.form['city']
    artist_obj.state = request.form['state']
    artist_obj.phone = request.form['phone']
    artist_obj.genres = request.form.getlist('genres')
    artist_obj.facebook_link = request.form['facebook_link']

    artist_obj.image_link = request.form['image_link']
    artist_obj.website = request.form['website']
    seeking = request.form['seeking_venue']
    artist_obj.seeking_venue = True if seeking == "YES" else False
    artist_obj.seeking_description = request.form['seeking_description']
    db.session.commit()
    flash('The artist has been updated successfully.')
  except ValueError as e:
    flash('It was not possible to update this Artist !')

  return redirect(url_for('show_artist', artist_id=artist_id))


#  ----------------------------------------------------------------
# Delete spicific artist from the database depending on artist_id:
# if you delete aa artist, all of its shows will be deleted
#  ----------------------------------------------------------------
@app.route('/artists/<artist_id>', methods=['POST'])
def delete_artist(artist_id):
  try:
    artist = Artist.query.filter_by(id=artist_id).first_or_404()
    db.session.delete(artist)
    db.session.commit()
    flash('The artist has been removed together with all of his shows.')
    return render_template('pages/home.html')
  except ValueError as e:
    flash('It was not possible to delete this artist')
  return None


#  ----------------------------------------------------------------
#                        Shows Controllers
#  ----------------------------------------------------------------


#  ----------------------------------------------------------------
# Display all shows:
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  data = []
  # get all shows information, by joining Show, Artist and Venue tables
  shows_results = db.session.query(Show).join(Artist).join(Venue).all()

  # this loop will pass on every show to get detailed information about is,
  # such as: start_time, venue information, and artist information
  for show_info in shows_results:
    data.append({
      "venue_id": show_info.venue_id,
      "venue_name": show_info.venue.name,
      "artist_id": show_info.artist_id,
      "artist_name": show_info.artist.name,
      "artist_image_link": show_info.artist.image_link,
      "start_time": show_info.start_time.strftime(' %y-%m-%d  %H:%M:%S ')
    })

  return render_template('pages/shows.html', shows=data)


#  ----------------------------------------------------------------
#  Create a new show:
#  ----------------------------------------------------------------
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    # get the information in the form that the user filled out
    start_time = request.form['start_time']
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']

    # create a new show object and add it to the postgres database (fyyurdb)
    show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()

  if error:
    flash('An error occurred. Show could not be listed.')

  return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
  return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
  return render_template('errors/500.html'), 500


if not app.debug:
  file_handler = FileHandler('error.log')
  file_handler.setFormatter(
    Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
  )
  app.logger.setLevel(logging.INFO)
  file_handler.setLevel(logging.INFO)
  app.logger.addHandler(file_handler)
  app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
  app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''