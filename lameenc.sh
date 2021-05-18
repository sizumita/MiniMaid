Unamem="`uname -m`"
Basedir="`pwd`"
if [[ $Unamem =~ .*(Arm|arm|arch).* ]]; then
  cd /tmp
  git clone https://github.com/chrisstaite/lameenc
  cd lameenc
  mkdir build
  cd build
  cmake ..
  make
  ls
  python -m pip install lameenc-1.3.1*.whl
  cd /tmp
  rm -rf lameenc
else
  python -m pip install lameenc
fi
cd $Basedir
