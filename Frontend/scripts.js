const form = document.querySelector('#my-form');

async function selectImage() {  
  // Get data URI of the selected image
  const photoField = fileSelect.files[0];
  const dataUri = await dataUriFromFormField(photoField);
  
  const imgEl = document.createElement('img');
  imgEl.addEventListener('load', () => {
    const resizedDataUri = resizeImage(imgEl, 300);
    document.querySelector('#img-preview').src = resizedDataUri;
    base64String = resizedDataUri.replace("data:", "").replace(/^.+,/, "");
    uploadFile(base64String)
  });
  imgEl.src = dataUri;
}


function dataUriFromFormField (field) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    
    reader.addEventListener('load', () => {
      resolve(reader.result);
    });
    
    reader.readAsDataURL(field);
  });
}

function resizeImage (imgEl, wantedWidth) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  const aspect = imgEl.width / imgEl.height;

  canvas.width = wantedWidth;
  canvas.height = wantedWidth / aspect;

  ctx.drawImage(imgEl, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL();
}

async function uploadFile(file) {
  var $alert = $('.alert');
  let formData = new FormData();
  formData.append("filename", 'image')
  formData.append("filedata", file)

  $.ajax('https://xxlkbgor75nvr7qw256z2xnrdm0ppqai.lambda-url.us-east-2.on.aws/image', {
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false,
              
      success: function (data) {
          $alert.hide();
          document.getElementById('result').innerHTML = data.category
          updateTable(data.confs)
          },
      error: function () {
          $alert.show();
          }
  });
}

function updateFileName(input) {
  if (input.files && input.files[0]) {
    document.getElementById('fileName').innerText = input.files[0].name;
  } else {
    document.getElementById('fileName').innerText = 'Select Image';
  }

}

function updateTable(object){
  var table = document.getElementById("table");
  $("#table").find("tr:not(:first)").remove();

  var count = 1
  for(property in object){
    var row = table.insertRow();
    var pos = row.insertCell(0);
    var name = row.insertCell(1);
    var conf = row.insertCell(2);

    pos.innerHTML = count++;
    name.innerHTML = `${object[property].name}`;
    conf.innerHTML = `${object[property].conf}%`;
  }
}