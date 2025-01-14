ARG NGINX_VER
FROM nginx:${NGINX_VER}-alpine
# ARG PHPMYADMIN_VER
COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html
# https://github.com/phpmyadmin/docker/issues/284#issuecomment-625468269
# must be something wrong with scoping on PHPMYADMIN_VER, but will need to look at this later. see https://stackoverflow.com/questions/43473236/docker-build-arg-and-copy#comment107312537_43473956
# COPY --from=phpmyadmin/phpmyadmin:${PHPMYADMIN_VER}-fpm /var/www/html /usr/share/nginx/html
COPY --from=phpmyadmin/phpmyadmin:5.2.1-fpm /var/www/html /usr/share/nginx/html