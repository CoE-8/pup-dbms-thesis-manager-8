$(function(){
	var keywords = [];

	function onFormSubmit(event) {
		var data = $(event.target).serializeArray();
		var thesis_data = {};
		for (var i = 0; i < data.length; i++) {
			var key = data[i].name;
			var value = data[i].value;
			thesis_data[key] = value; 
		}
		var thesis_create_api = '/api/handler';
		$.post(thesis_create_api, thesis_data, function(response)
		{
			if (response.status == 'OK')
			{	
				alert('Thesis successfully created.');
				$(location).attr('href', '/thesis/list');
				return true;
			}
			else
			{
				alert(response.status);
				return false;
			}
		})
		return false;
	}

	function onRegFormSubmit(event) {
		var data = $(event.target).serializeArray();
		var user_data = {};
		for (var i = 0; i < data.length; i++) {
			var key = data[i].name;
			var value = data[i].value;
			user_data[key] = value; 
		}
		var register_api = '/register';
		$.post(register_api, user_data, function(response)
		{	
			if (response.status == 'OK')
			{
				alert('Registration successful!');
				$(location).attr('href', '/');
				return true;
			}
			else alert(response.status);
		})
		return false;
	}

	function loadAllThesis(event) 
	{
		$('ul.thesis_list').empty()
		year = $('#filter_year').val()
		adviser = $('#filter_adviser').val()
		university = $('#filter_university').val()
		var thesis_list_api = '/api/handler';
		$.get(thesis_list_api, {'year': year,'university':university,'adviser':adviser} ,function(response)
		{
			if (response.status == 'OK')
			{
				response.data.forEach(function(thesis) {
				var thesis_info = thesis.thesis_year + "   |   " + thesis.thesis_title + "   |   " + thesis.f_first_name + " " + thesis.f_last_name;
				$('ul.thesis_list').append('<li>'+thesis_info+' <a class="mybtn" href=\'/thesis/edit/'+thesis.self_id+'\'>Edit</a><a class=\'mybtn\' href=\'/thesis/delete/'+thesis.self_id+'\'>Delete</a><hr style="margin-top: 5px;"></li>');
				return false;
				})
			}
			else 
			{$('ul.thesis_list').append('<li>No thesis found<li>');return false;}
		})
	}
	function createStud(event) {
		var data = $(event.target).serializeArray();
		var student_data = {};
		var thesis = []

		for (var i = 0; i < data.length; i++) {
			var key = data[i].name;
			if (key.indexOf('thesis') > -1)
			{
				var title = data[i].value;
				thesis.push(title)
			}
			var value = data[i].value;
			student_data[key] = value;
		}

		var student_create = '/student/create';
		$.post(student_create, JSON.stringify({ "student_data": student_data,"thesis":thesis}), function(response)
		{	
			if (response.status == 'OK')
			{
				alert("Student successfully created.");
				$(location).attr('href', '/student/list');
				return true;
			}
			else
			{
				alert(response.status);
			}
		})
		return false;
	}

	function createFac(event) {
		var data = $(event.target).serializeArray();
		var faculty_data = {};
		var thesis = []
		for (var i = 0; i < data.length; i++) {
			var key = data[i].name;
			if (key.indexOf('thesis') > -1)
			{
				var title = data[i].value;
				thesis.push(title)
			}
			var value = data[i].value;
			faculty_data[key] = value;
		}
		var faculty_create = '/faculty/create';
		$.post(faculty_create, JSON.stringify({ "faculty_data": faculty_data,"thesis":thesis}), function(response)
		{	
			if (response.status == 'OK')
			{
				alert("Faculty successfully created.");
				$(location).attr('href', '/faculty/list');
				return true;
			}
			else
			{
				alert(response.status);
			}
		})
		return false;
	}

	function createUniv(event) {
		var data = $(event.target).serializeArray();
		var univ_data = {};

		for (var i = 0; i < data.length; i++) {
			var key = data[i].name;
			var value = data[i].value;
			univ_data[key] = value;
		}
		
		var univ_create = '/university/create';
		$.post(univ_create, univ_data, function(response)
		{	
			if (response.status == 'OK')
			{
				alert("university successfully created.");
				$(location).attr('href', '/university/list');
				return true;
			}
			else
			{
				alert(response.status);
			}
		})
		return false;
	}

	function createCol(event) {
		var data = $(event.target).serializeArray();
		var col_data = {};

		for (var i = 0; i < data.length; i++) {
			var key = data[i].name;
			var value = data[i].value;
			col_data[key] = value;
		}
		
		var col_create = '/college/create';
		$.post(col_create, col_data, function(response)
		{	
			if (response.status == 'OK')
			{
				alert("College successfully created.");
				$(location).attr('href', '/college/list');
				return true;
			}
			else
			{
				alert(response.status);
			}
		})
		return false;
	}

	function createDep(event) {
		var data = $(event.target).serializeArray();
		var dept_data = {};

		for (var i = 0; i < data.length; i++) {
			var key = data[i].name;
			var value = data[i].value;
			dept_data[key] = value;
		}
		
		var dept_create = '/department/create';
		$.post(dept_create, dept_data, function(response)
		{	
			if (response.status == 'OK')
			{
				alert("department successfully created.");
				$(location).attr('href', '/department/list');
				return true;
			}
			else
			{
				alert(response.status);
			}
		})
		return false;
	}
	
	$('form#form1').submit(onFormSubmit);
	$('form#registration').submit(onRegFormSubmit);
	$('#list_thesis').click(loadAllThesis);
	$('form#stud_create').submit(createStud);
	$('form#fac_create').submit(createFac);
	$('form#univ_create').submit(createUniv);
	$('form#col_create').submit(createCol);
	$('form#dept_create').submit(createDep);
});

	var List = new List('test-list', {
	  valueNames: ['name'],
	  page: 10,
	  plugins: [ ListPagination({}) ] 
	});