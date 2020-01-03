===========================================
Administrator's Guide
===========================================

**routetility** is the name for a database to handle running routes which are stored on steeplechasers.org. **routetility**
imports gpx files created by other tools (e.g., MapMyRun), and renders a user interface with a map and table for all
the routes, individual route with map and elevation, directions to the starting point, and turn by turn directions.

This guide instructions a **routetility**  administrator how to create and update routes in this database.

To become a routetility  administrator, you must have be configured into the tool. If you get error messages, or can’t
get past the Please Sign In screen during Logging In, please contact technology@steeplechasers.org for access.


Adminstrator's Manual
==================================

Interest Admin
+++++++++++++++
An :term:`interest admin` can create and edit :term:`routes <route>` for one or more :term:`interests <interest>`,
as set up by a :term:`super admin`.

.. _access-admin-page:

Access the Admin Page
----------------------------------------

Navigate to https://routes.loutilities.com/admin or navigate to https://routes.loutilities.com, then scroll down and
click the **Admin** link near the bottom of the page.

.. _logging-in:

Logging In
--------------------------------------
After your user is created, the :term:`super admin` will send an email to you to reset your password. Follow the
instructions to set your password.

When you are not logged in, you will see a page similar to what is shown below. Click the **Log In** button, then
enter the email address you received the password reset email on. If you forgot your **routetility** password, you can
be sent an email to reset this.

.. image:: images/login.*
   :align: center


.. _select-interest:

Select Interest
-----------------------------------------
After logging in, you'll see a fairly empty page with navigation on the left and a pull-down near the top. This
pull-down can be used to select the :term:`interest` you'll be working on. The last :term:`interest` you choose will
be automatically selected the next time you log in, but this may need to be selected the first time you use the
system.

.. image:: images/select-interest.*
   :align: center


.. _edit-routes:

Edit Routes View
-----------------------------------------
Click **Edit Routes** on the navigation to get to this view.

The Edit Routes view allows you to page through the available :term:`routes <route>`. A Search box allows the table to be filtered
down to the rows which contain that text. For instance, if you’d like to search for :term:`routes <route>` with Baker Park in the
name, just type in Baker Park in the search box.

.. image:: images/edit-routes.*
   :align: center

.. _add-route:

Add Route
-----------------------------------------
Before adding a route, it seems reasonable to check to see that the route isn’t already in the database. This can be
done in the user interface (https://routes.loutilities.com). You should check routes of about that distance which start in
the same location. Note you can sort the route table by distance by clicking on the arrow next to the miles heading.

To add a route, from the admin view, click the **New** button. You will see a Create form. In another window, bring up
MapMyRun, Strava, Garmin Connect, RunningAHEAD or other application where you’ll pull the route from. These instructions
assume MapMyRun, but any application from which you can download a gpx file will work. For details on how to download
a GPX file, see :ref:`download-gpx-file`.

Enter the fields as described, then click **Create** after Processing disappears from File button.


    Route Name
        Name of the route, could be the same as what is used in MapMyRun. We suggest using mixed case, not all capitals,
        though.

    Description
        Optional short description, e.g., where to meet. E.g., "Meet in front of Zi Pani".


    Surface
        Choose road, trail or mixed.

    Route URL
        Copy the URL to access the route from MapMyRun. This is for information only, but it’s nice to know where the
        data came from.

    Turns
        Copy / paste or type the turn by turn directions into this window. You’ll need a carriage return between
        each turn. It’s ok if the lines wrap after pasting or when typing. Pasting from an email may give extra
        carriage returns, but don’t worry about this.

    File
        Select the GPX file downloaded from MapMyRun. Note when you select the file, it takes a bit of time for it
        to upload and do some calculations/processing.

    Start Location
        This defaults to the first point in the GPX file. This provides a destination for the driving directions
        for the user. You can change this to an address if you’d like, but please check that what you type will work
        in a google maps search. Probably best to leave this alone.

    Distance (miles)
        This is calculated from the gpx file. You can change this if you’d like. E.g., if you see 19.9 or 20.1 you might
        want to change the field to 20.

    Elev Gain (ft)
        This is calculated from the gpx file. This can be changed but again probably best to leave this alone.

.. image:: images/new-route.*
   :align: center


.. _edit-route:

Edit Route
-----------------------------------------
To edit a route, select the route you want to edit, then click **Edit**. When you are done with your edits click **Update**.
If changing File click **Update** after Processing disappears from File button.

The Edit form has all the same fields as the Create form, and one additional field.

    Active
        If you want to make the route so the user won’t see it, change Active from “active” to “deleted”. This is done
        this way so we can add it back later if we want.

.. image:: images/edit-route.*
   :align: center


.. _download-gpx-file:

Download GPX File
+++++++++++++++++++++++
This section shows how to download GPX file from various applications.

For all of these we suggest when you download the GPX file you name the file the same as the Route Name you chose.


.. _mapmyrun:

MapMyRun
--------------------------------------
Bring up the route you want to download. Click **MORE** on top of map. Click **DOWNLOAD GPX**. Name the file the
same name as the route.

.. image:: images/mapmyrun.*
   :align: center


.. _strava:

Strava
--------------------------------------
Bring up the activity you want to download. Click the **ellipses** link under Laps on the left. Click **Export GPX**. Name
the file the same name as the route.

.. image:: images/strava.*
   :align: center


.. _garmin-connect:

Garmin Connect
--------------------------------------
Bring up the activity you want to download. Click on the Settings **gear** button on the top right. Click **Export to
GPX**. Name the file the same name as the route.

.. image:: images/garmin-connect.*
   :align: center


.. _runningahead:

RunningAHEAD
--------------------------------------
Bring up the workout you want to download. Click the **hamburger / menu** button next to the run type. Click
**Download GPX**. Name the file the same name as the route.

.. image:: images/runningahead.*
   :align: center


.. _super-admin:

Super Admin
+++++++++++++++
A super admin can create users, create :term:`interests <interest>`, assign user roles,
:term:`interests <interest>`, etc.

.. todo:: This section needs additional work.

.. _create-new-user:

Create a New User
--------------------------------------

From User/Roles > Users, create new user

From /reset type in new user's email address, then click **Recover Password**


.. _known-problems:

Known Problems / Planned Enhancements
=========================================
See https://github.com/louking/runningroutes/issues

Contact technology@steeplechasers.org if any other problems are noticed, or if you’d like to see any enhancements.


