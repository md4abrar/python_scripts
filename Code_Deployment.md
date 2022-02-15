git clone $GITHUB_URL

sudo apt-get install virtualenv

cd onboarding-app  # look for exact repo name using ls -lrt

virtualenv venv -p /usr/bin/python3

. venv/bin/activate

# Install these dependancies
sudo apt-get install build-essential python3-dev
pip install cython
pip install --no-binary :all: falcon

# Note : you might see few errors here.. look clearly why it is failing and install any other dependencies required

pip install gunicorn

gunicorn -b 0.0.0.0:5000 main:app --reload  # Replace main:app with your main function ...
