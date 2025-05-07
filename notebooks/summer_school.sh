#!/bin/bash

su - jovyan <<'EOF'
echo "Today is " `date`
mkdir /home/jovyan/education/hyytiala-practicals
git clone https://git.wur.nl/peter050/hyytiala-practicals.git /home/jovyan/education/hyytiala-practicals/.
ln -s /home/jovyan/education/hyytiala-practicals/EXERCISES -t /home/jovyan/education/Summer-school/.
ln -s /home/jovyan/education/hyytiala-practicals/MEASUREMENTS -t /home/jovyan/education/Summer-school/.
rsync -auv /home/jovyan/education/hyytiala-practicals/MODEL/ /home/jovyan/education/Summer-school/build/MODEL/
rsync -auv /home/jovyan/education/hyytiala-practicals/MODEL_ext/ /home/jovyan/education/Summer-school/build/MODEL_ext/

cd /home/jovyan/education/Summer-school/build/MODEL && make clean && make
cd /home/jovyan/education/Summer-school/build/MODEL_ext && make clean && make

cd /home/jovyan/education/Summer-school/build/MODEL_ext
./MOGUNTIA < basefunct_gl
./MOGUNTIA < basefunct_nh
./MOGUNTIA < basefunct_tr
./MOGUNTIA < basefunct_sh
./MOGUNTIA < basefunct_base
echo "Done"
EOF


# Run the original entry point script.
exec /usr/local/bin/start-notebook.sh "$@"
