/*
    TODO:
    #) alert errors when fetching package versions
    #) add github
    #) add config file
    #) change app creation
    #) adding custom tables, not just User, foreign keys
    #) adding background workers
    #) frontend
*/

var app = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        projectName: '',
        addDatabase: false,
        addAuthSys: false,
        virtEnv: {
            show: false,
            name: 'venv',
            params: [
                { name: 'systemSitePackages', value: false },
                { name: 'clear', value: false },
                { name: 'pip', value: true }
            ],
        },
        requirements: [
            { name: 'flask', version: '2.0.1', type: '=='},
        ],
        dbType: '',
        authSys: {
            userTableName: 'User',
            userTableFields: [
                { name: 'id', pk: true, nullable: false, type: 'Integer', unique: true },
                { name: 'name', pk: false, nullable: false, type: 'String', unique: true },
                { name: 'email', pk: false, nullable: false, type: 'String', unique: true },
                { name: 'password', pk: false, nullable: false, type: 'String', unique: false }
            ],
            lastFieldFilled: true,
            loginView: 'login',
        },
        wtForms: {
            show: false,
            useCsrf: true,
            asMainFile: true,
            forms: [
                { 
                    // https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Flask_Blog/03-Forms-and-Validation/forms.py
                    // https://flask-wtf.readthedocs.io/en/0.15.x/quickstart/#creating-forms
                    name: 'RegistrationForm',
                    lastFieldFilled: true,
                    fields: [
                        { name: 'username', label: 'Username', validators: [], type: 'StringField' },
                        { name: 'email', label: 'Email', validators: [], type: 'StringField' },
                        { name: 'password', label: 'Password', validators: [], type: 'PasswordField' },
                        { name: 'confirm_password', label: 'Confirm Password', validators: ["EqualTo('password')"], type: 'PasswordField' }
                    ] 
                },
            ],
            validators: [
                { name: 'EqualTo', param: '', use: false },
                { name: 'Length', min: '', max: '', use: false },
                { name: 'DataRequired', use: false },
                { name: 'Email', use: false },
                { name: 'Optional', use: false },
                { name: 'NumberRange', min: '', max: '', use: false },
                { name: 'InputRequired', use: false },
                { name: 'MacAddress', use: false },
                { name: 'IPAddress', use: false },
                { name: 'Regexp', param: '', use: false },
                { name: 'URL', param: '', use: false }
            ],
            selectedValidators: [],
        },
        emails: {
            show: false
        },
        blueprints: {
            show: false,
            lastFieldFilled: true,
            blueprintsList: [
                { name: 'users', addForms: false, forms: [] }
            ],
        },
        frontend: {
            show: false,
            addCss: true,
            addJs: true,
            layout: true,
            index: true
        },
    },
    methods: {
        removeElementFromArray: function(array, element) {
            array.splice(array.indexOf(element), 1);
        },
        extendArrayByElement: function(array, element, avoidDuplicates = false) {
            if (avoidDuplicates) {
                if (!array.includes(element)) array.splice(array.length, 1, element);
            }
            else array.splice(array.length, 1, element);
        },
        sendData: function() {
            fetch(`${window.origin}/create`, {
                method: "POST",
                body: JSON.stringify(this.$data),
                headers: new Headers({
                  "content-type": "application/json"
                })
            })
            .then(function (response) {
                if (response.status !== 200) {
                    alert(`Looks like there was a problem. Status code: ${response.status}`);
                    return;
                }
                
                response.json().then(function(data) {
                    
                });
                
            })
            .catch(function (error) {
                console.log("Fetch error: " + error);
            });
        },
        setValidators: function(field) {
            // convert objects from selectedValidators to strings and then append
            field.validators.splice(0);
            this.wtForms.selectedValidators.forEach(validator => {
                let args = ''
                if (validator.param) { args += `'${validator.param}'`; }
                else if (validator.min) { args += `min = ${validator.min}, max = ${validator.max}`; }
                field.validators.push(validator.name + '(' + args + ')');
            });
        },
        updateSelectedValidators: function(validator) {
            if (this.wtForms.selectedValidators.includes(validator)) {
                // remove validator
                this.wtForms.selectedValidators.splice(this.wtForms.selectedValidators.indexOf(validator), 1);
                validator.use = false;
            }
            else {
                // add validator
                this.wtForms.selectedValidators.splice(this.wtForms.selectedValidators.length, 1, validator);
                validator.use = true;
            }
        },
        resetValidatorsConfiguration: function() {
            // clear array and reset all use fields
            this.wtForms.selectedValidators.splice(0);
            this.wtForms.validators.forEach(validator => { 
                validator.use = false;
                validator.min ? validator.min = '' : validator;
                validator.max ? validator.max = '' : validator;
                validator.param ? validator.param = '' : validator;
            });
        },
        getLatestPackageVersion: function (package) {
            fetch(`https://pypi.org/pypi/${package.name}/json`, {
                method: "GET"
            })
            .then(function (response) {
                if (response.status !== 200) {
                    alert(`Looks like there was a problem. Status code: ${response.status}`);
                    return;
                }
                response.json().then(function(data) {
                    const releases = data['releases'];
                    const latestVersion = Object.keys(releases)[Object.keys(releases).length - 1];
                    package.version = latestVersion;
                });
            })
            .catch(function (error) {
                console.log("Fetch error: " + error);
            });
        },
    },
    watch: {
        'authSys.userTableFields': {
            handler: function() {
                this.authSys.lastFieldFilled = checkLastField(this.authSys.userTableFields);
            }
        },
        dbType: function() {
            console.log(this.dbType);
        },
        addAuthSys: {
            handler: function() {
                const packages = [
                    { name: 'Flask-Login', version: '0.5.0', type: '==' }, 
                    { name: 'Bcrypt-Flask', version: '1.0.1', type: '==' }
                ];
                handlePackages(this.requirements, packages, this.addAuthSys);
                if (!this.wtForms.forms.some(e => e.name === 'LoginForm')) {
                    this.extendArrayByElement(this.wtForms.forms, { 
                        name: 'LoginForm', 
                        fields: [
                            { name: 'email', label: 'Email', validators: ['DataRequired()'], type: 'StringField' },
                            { name: 'password', label: 'Password', validators: ['DataRequired()'], type: 'PasswordField' },
                        ]  
                    });
                }
            },
            deep: true
        },
        addDatabase: {
            handler: function() {
                const packages = [
                    { name: 'Flask-SQLAlchemy', version: '2.5.1', type: '=='}
                ];
                handlePackages(this.requirements, packages, this.addDatabase);
            },
            deep: true
        },
        'wtForms.show': {
            handler: function() {
                const package = [ { name: 'Flask-WTF', version: '2.3.3', type: '==' } ];
                handlePackages(this.requirements, package, this.wtForms.show);
            }
        },
        'wtForms.forms': {
            handler: function() {
                for (let i = 0; i < this.wtForms.forms.length; i++) {
                    this.wtForms.forms[i].lastFieldFilled = checkLastField(this.wtForms.forms[i].fields);
                }
            },
            deep: true
        },
        'authSys.userTableName': {
            handler: function() {
                this.authSys.userTableName = stringToCamelCase(this.authSys.userTableName);
            }
        },
        'blueprints.blueprintsList': {
            handler: function() {
                this.blueprints.lastFieldFilled = checkLastField(this.blueprints.blueprintsList);
            },
            deep: true
        },
        'emails.show': {
            handler: function() {
                const packages = [
                    { name: 'Flask-Mail', version: '0.9.1', type: '=='}
                ];
                handlePackages(this.requirements, packages, this.emails.show);
            },
            deep: true
        },
    },
    computed: {
        normalizeFormName() {
            return this.wtForms.forms.map(function(form) {
                form.name = stringToCamelCase(form.name);
            });
        },
    }
})

// Function to check if package is already included and add/delete (based on boolean value)
// requirements and packages are lists, condition is boolean
function handlePackages(requirements, packages, condition) {
    // adding packages
    if (condition === true) {
        // Looping over packages to add
        for (let i = 0; i < packages.length; i++) {
            let found = false;
            // Looking in requirements list
            requirements.forEach(package => package.name === packages[i].name ? found = true : package);
            if (!found) {
                requirements.push(packages[i]);
            }
        }
    }
    // removing packages
    else {
        for (let i = 0; i < packages.length; i++) {
            requirements.forEach(package => package.name === packages[i].name ? requirements.splice(requirements.indexOf(package), 1) : package);
        }
    }
}

// Checks if last element of list of inputs is empty
// input empty -> return false
// input filled -> return true
function checkLastField(list) {
    if (list.length < 1) { return true; }
    let lastEl = list[list.length - 1].name;
    if (lastEl === "" || lastEl === undefined) {
        return false;
    }
    else { return true; }
}

// converts string to its camel case representation
function stringToCamelCase(string) {
    let workString = string.trim();
    if (workString.includes(' ') && workString.length > 0) {
        workString = workString[0].toUpperCase() + workString.substring(1, workString.indexOf(' ') + 1) + workString[workString.indexOf(' ') + 1].toUpperCase() + workString.substring(workString.indexOf(' ') + 2);
        return workString.split(' ').join('');
    }
    else {
        return string;
    }
}
