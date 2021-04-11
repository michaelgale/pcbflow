convert -density 1200 $1/$1_preview_bot.pdf -resize 800x600 $1/$1_preview_bot.png
convert -density 1200 $1/$1_preview_top.pdf -resize 800x600 $1/$1_preview_top.png
convert -density 1200 $1/$1_preview_top_docu.pdf -resize 800x600 $1/$1_preview_top_docu.png
convert -density 1200 $1/$1_preview_bot_docu.pdf -resize 800x600 $1/$1_preview_bot_docu.png
convert -density 1200 $1/$1_preview_all.pdf -resize 800x600 $1/$1_preview_all.png
mv $1/$1_preview_top.png ../../images/
mv $1/$1_preview_bot.png ../../images/
mv $1/$1_preview_all.png ../../images/
mv $1/$1_preview_top_docu.png ../../images/
mv $1/$1_preview_bot_docu.png ../../images/