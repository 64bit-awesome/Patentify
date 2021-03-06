The frontend was bootstrapped with React.
  
## Testing the App Locally
In the project directory, you can run:

### `npm start` or `yarn start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `yarn test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

## Deploying the App for Production

### `npm run build` or `yarn build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

To deploy simply copy all the files in the build folder over to a web-server directory. \
With Apache web-serever, simply copy the files over to `var/www/[virtual-host-name]/html/` and any other folders if other <VirtualHosts> are configured.

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `yarn eject`

**Note: this is a one-way operation. Once you `eject`, you can’t go back!**

If you aren’t satisfied with the build tool and configuration choices, you can `eject` at any time. This command will remove the single build dependency from your project.

Instead, it will copy all the configuration files and the transitive dependencies (webpack, Babel, ESLint, etc) right into your project so you have full control over them. All of the commands except `eject` will still work, but they will point to the copied scripts so you can tweak them. At this point you’re on your own.

You don’t have to ever use `eject`. The curated feature set is suitable for small and middle deployments, and you shouldn’t feel obligated to use this feature. However we understand that this tool wouldn’t be useful if you couldn’t customize it when you are ready for it.
  
## Proper Apache Configuration to Run Node.js React App
Enable RewriteEngine:
```
a2emod rewrite
systemctl restart apache2
```
Allow rewrites on the directory where the app is hosted by modifying /etc/apache2/apache2.conf
```
<Directory /var/www/[virtual-host-name]/>
  AllowOverride All
  Require all granted
</Directory>
```
Add .htaccess file in the virtual host root:
```
Options -MultiViews
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^ index.html [QSA,L]
```
Finally:
```
systemctl restart apache2
```

^ this will redirect all requests to index.html so that React can take care of them. \
^ without any of the above direct link access and redirects will result in 404 errors.


## Learn More

### [Code Splitting](https://facebook.github.io/create-react-app/docs/code-splitting)

### [Analyzing the Bundle Size](https://facebook.github.io/create-react-app/docs/analyzing-the-bundle-size)

### [Making a Progressive Web App](https://facebook.github.io/create-react-app/docs/making-a-progressive-web-app)

### [Advanced Configuration](https://facebook.github.io/create-react-app/docs/advanced-configuration)

### [Deployment](https://facebook.github.io/create-react-app/docs/deployment)

### [`yarn build` fails to minify](https://facebook.github.io/create-react-app/docs/troubleshooting#npm-run-build-fails-to-minify)

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started). \
To learn React, check out the [React documentation](https://reactjs.org/).
