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
from forms import *
from flask_migrate import Migrate
import sys
from sqlalchemy import func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data =[]
    locations = db.session.query(Venue.city,Venue.state,func.count()).group_by(Venue.city,Venue.state)
    now = datetime.now() 
    for location in locations:
        venues = db.session.query(Venue.id,Venue.name).filter(Venue.city==location.city).all()
        venues_list =[]
        for venue in venues:
            upcoming_shows_results = db.session.query(Show).join(Artist).filter(Show.venue_id==venue.id).filter(Show.start_time>now).all()
            venues_list.append({
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_shows":len(upcoming_shows_results)
            })
        data.append({
          "city":location.city,
          "state":location.state,
          "venues": venues_list
        })
        
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term=request.form.get('search_term', '')
  search = "%{}%".format(search_term)
  venues = Venue.query.filter(Venue.name.ilike(search)).all()
  
  data = []

  now = datetime.now()  
  for venue in venues:
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > now).all()),
    })

  response={
    "count": len(venues),
    "data": data
    }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  past_shows = []
  upcoming_shows = []
  now = datetime.now()
  venue = Venue.query.get(venue_id)

  past_shows_results = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<now).all()
  upcoming_shows_results = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>now).all()

  for past_show in past_shows_results:
    past_shows.append({
      "artist_id": past_show.artist_id,
      "artist_name": past_show.artist.name,
      "artist_image_link": past_show.venue.image_link,
      "start_time": past_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for upcoming_show in upcoming_shows_results:
    upcoming_shows.append({
      "artist_id": upcoming_show.artist_id,
      "artist_name": upcoming_show.artist.name,
      "artist_image_link": upcoming_show.venue.image_link,
      "start_time": upcoming_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
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
    "upcoming_shows_count": len(upcoming_shows),
  }


  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        name = request.form['name']
        genres = request.form.getlist('genres')
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        facebook_link = request.form['facebook_link']
        website = request.form['website']
        seeking_talent = True if 'seeking_talent' in request.form else False 
        seeking_description = request.form['seeking_description']
        image_link = request.form['image_link']

        venue = Venue(name=name,genres=genres,city=city,state=state,address=address,phone=phone,facebook_link=facebook_link,
        website=website,seeking_talent=seeking_talent,seeking_description=seeking_description,image_link=image_link)

        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    #if error: 
     #   flash('Venue ' + request.form['name'] + ' was successfully listed!')
    #if not error: 
     #   flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  if error: 
      flash('An error occurred. The venue could not be deleted.')
  if not error: 
      flash('The Venue was successfully deleted.')
  return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
    
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  error = False  
  venue = Venue.query.get(venue_id)
  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_talent = request.form['seeking_talent'] 
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('An error occurred. The venue could not be updated.')
  if not error: 
    flash('The venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  search_term=request.form.get('search_term', '')
  
  search = "%{}%".format(search_term)
  artists = Artist.query.filter(Artist.name.ilike(search)).all()

  data = []

  now = datetime.now()  
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > now).all()),
    })
  
  response={
    "count": len(artists),
    "data": data
 }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  past_shows = []
  upcoming_shows = []
  now = datetime.now()
  artist = Artist.query.get(artist_id)
  past_shows_results = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<now).all()
  upcoming_shows_results = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>now).all()

  for past_show in past_shows_results:
    past_shows.append({
      "venue_id": past_show.venue_id,
      "venue_name": past_show.venue.name,
      "artist_image_link": past_show.venue.image_link,
      "start_time": past_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for upcoming_show in upcoming_shows_results:
    upcoming_shows.append({
      "venue_id": upcoming_show.venue_id,
      "venue_name": upcoming_show.venue.name,
      "artist_image_link": upcoming_show.venue.image_link,
      "start_time": upcoming_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

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
    "upcoming_shows_count": len(upcoming_shows),
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  error = False  
  artist = Artist.query.get(artist_id)

  try: 
    artist.name = request.form['name']
    artist.genres = request.form.getlist('genres')
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.website = request.form['website']
    artist.facebook_link = request.form['facebook_link']
    artist.seeking_venue = request.form['seeking_venue'] 
    artist.seeking_description = request.form['seeking_description']
    artist.image_link = request.form['image_link']
    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash('An error occurred. The artist ' + artist.name+' could not be updated')
  if not error: 
    flash('Artist ' + artist.name + ' was successfully updated!')


  return redirect(url_for('show_artist', artist_id=artist_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try: 
      name = request.form['name']
      genres = request.form.getlist('genres')
      city = request.form['city']
      state = request.form['state']
      phone = request.form['phone']
      facebook_link = request.form['facebook_link']
      website = request.form['website']
      seeking_venue = True if 'seeking_venue' in request.form else False 
      seeking_description = request.form['seeking_description']
      image_link = request.form['image_link']

      artist = Artist(name=name, genres=genres,city=city, state=state, phone=phone, website=website, 
      seeking_venue=seeking_venue, seeking_description=seeking_description,facebook_link=facebook_link, image_link=image_link)
      db.session.add(artist)
      db.session.commit()
  except: 
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally: 
      db.session.close()
  if error: 
      flash('An error occurred. Artist ' + request.form['name']+ ' could not be listed.')
  if not error: 
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  get_shows = db.session.query(Show).join(Artist).join(Venue).all()
  data = []
  for show in get_shows: 
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name, 
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try: 
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except: 
     db.session.rollback()
     error = True
     print(sys.exc_info)
  finally: 
    db.session.close()
  if error: 
    flash('An error occurred. The show could not be listed.')
  if not error: 
    flash('The show was successfully listed')
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
